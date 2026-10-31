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
    page: int       # 1-based PDF page number (not the printed page label)


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
        for i, piece in enumerate(split_page(text)):
            out.append(Chunk(
                chunk_id=f"{pdf_path.stem}::p{page_no}::c{i}",
                text=piece, pub=pub, title=title, file=pdf_path.name, page=page_no,
            ))
    return out


def cite(meta: dict) -> str:
    """How a source is named to the reader and to the model: 'ATP 3-35, p. 42'."""
    return f"{meta['pub']}, p. {meta['page']}"


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
