"""Shared pieces for OS DAGGER: where the index lives, how a PDF becomes chunks,
and how a chunk is cited.

Nothing here talks to a model. Retrieval is fully local.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCTRINE_DIR = ROOT / "doctrine"
INDEX_DIR = ROOT / "index"
COLLECTION = "doctrine"

# Chunking. A chunk never crosses a page boundary, so every citation carries a
# real page number that a reader can open and check.
CHUNK_CHARS = 1500
CHUNK_OVERLAP = 200
MIN_CHUNK_CHARS = 80  # pages that are only a figure or a header yield nothing


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    pub: str        # e.g. "ATP 3-35"
    title: str      # e.g. "Army Deployment and Redeployment"
    file: str       # file name inside doctrine/
    page: int       # 1-based PDF page number
    printed: str    # the page number printed on the page ("3-7", "vii", "12"), or "" if not found


_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"


def printed_page(text: str, pub: str) -> str:
    """Read the printed page number out of the running header or footer.

    Army publications print it on the same line as the pub number and date:
    '1-6 ATP 4-16 25 April 2022' or 'ADP 3-0 21 March 2025 27' or 'vii'.
    Only the first and last 300 characters of the page are searched, so a
    cross-reference in the body ("see paragraph 3-7") is never mistaken for it.
    """
    # "AR 600-20" is printed "AR 600–20" (en dash); a changed pub adds "(INCL C1)";
    # regulations put a bullet between pub and date.
    pub_re = re.escape(pub).replace(r"\ ", r"\s*").replace(r"\-", r"[-–‑]")
    pub_full = rf"{pub_re}(?:\s*\(INCL\s*C\d+\))?"
    sep = r"(?:\s*[•·]\s*|\s+)"
    date_re = rf"\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}"
    num = r"([A-Z]-\d{1,3}|\d{1,2}-\d{1,3}|\d{1,3}|[ivxlc]{1,6})"  # "B-2", "3-7", "27", "vii"
    head, tail = text[:300], text[-300:]
    for zone in (tail, head):
        z = re.sub(r"\s+", " ", zone)
        # number, then pub and date in either order
        m = (re.search(rf"\b{num}{sep}{pub_full}{sep}{date_re}", z)
             or re.search(rf"{pub_full}{sep}{date_re}{sep}{num}\b", z)
             or re.search(rf"{date_re}{sep}{pub_full}{sep}{num}\b", z)
             or re.search(rf"\b{num}{sep}{date_re}{sep}{pub_full}", z))
        if m:
            return m.group(1)
    # Some PDFs garble the header date into font codes ("0D\" for "May"). Fall back
    # to the number sitting right beside the pub number, header zone only.
    z = re.sub(r"\s+", " ", text[:150])
    m = re.search(rf"\b{num}\s+{pub_full}\b", z) or re.search(rf"\b{pub_full}\s+(?:\S{{1,12}}\s+)?{num}\b", z)
    return m.group(1) if m else ""


def pub_from_filename(name: str) -> tuple[str, str]:
    """'ATP_3-35_Army_Deployment_and_Redeployment_2023-03-09.pdf'
    -> ('ATP 3-35', 'Army Deployment and Redeployment').

    The date suffix and extension are dropped. Anything that does not follow the
    SERIES_NUMBER_Title_DATE pattern falls back to the bare file stem.
    """
    stem = Path(name).stem
    m = re.match(r"^([A-Z]+)_([0-9][0-9A-Za-z.\-]*)_(.+?)(?:_\d{4}(?:-\d{2}){0,2})?(?:_C\d+_\d{4}-\d{2}-\d{2})?$", stem)
    if not m:
        return stem, stem
    series, number, title = m.groups()
    title = re.sub(r"_\d{4}$", "", title).replace("_", " ")
    return f"{series} {number}", title


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_page(text: str) -> list[str]:
    """Split one page's text into overlapping chunks, preferring sentence ends."""
    text = clean_text(text)
    if len(text) < MIN_CHUNK_CHARS:
        return []
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        if end < len(text):
            # back up to the last sentence end inside the window, if one is near
            cut = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
            if cut > start + CHUNK_CHARS // 2:
                end = cut + 1
        piece = text[start:end].strip()
        if len(piece) >= MIN_CHUNK_CHARS:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def read_pdf_chunks(pdf_path: Path) -> list[Chunk]:
    """Every chunk of one PDF, page by page. Requires pypdf."""
    from pypdf import PdfReader

    pub, title = pub_from_filename(pdf_path.name)
    reader = PdfReader(str(pdf_path))
    out: list[Chunk] = []
    for page_no, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:  # a damaged page should not sink the whole pub
            text = ""
        label = printed_page(text, pub)
        for i, piece in enumerate(split_page(text)):
            out.append(Chunk(
                chunk_id=f"{pdf_path.stem}::p{page_no}::c{i}",
                text=piece, pub=pub, title=title, file=pdf_path.name, page=page_no, printed=label,
            ))
    return out


def cite(meta: dict) -> str:
    """How a source is named to the reader and to the model.

    Prefers the number printed on the page, which is how doctrine is quoted:
    'ATP 3-35, p. 3-7'. Falls back to the PDF page: 'ATP 3-35, PDF p. 42'.
    """
    if meta.get("printed"):
        return f"{meta['pub']}, p. {meta['printed']}"
    return f"{meta['pub']}, PDF p. {meta['page']}"


def locate(meta: dict) -> str:
    """Where to open the file: 'PDF page 42' (what a PDF reader's page box takes)."""
    return f"PDF page {meta['page']}"


def open_collection(create: bool = False):
    """The persistent Chroma collection. Embeddings are Chroma's default local
    model (all-MiniLM-L6-v2 through onnxruntime); it is downloaded once, about
    80 MB, into the user's cache. No API key is needed for retrieval.
    """
    import chromadb

    INDEX_DIR.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    if create:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
        return client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    return client.get_collection(COLLECTION)


def env_or(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default
