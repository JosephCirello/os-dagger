"""Build the OS DAGGER index: every PDF in doctrine/ becomes page-bound chunks
in a local Chroma collection under index/.

    python build_index.py            # full rebuild (safe to re-run)
    python build_index.py --check    # just report what would be indexed

No API key is used. The only network access is Chroma's one-time download of
its small local embedding model on the first run.
"""

from __future__ import annotations

import argparse
import sys
import time

from dagger_common import DOCTRINE_DIR, INDEX_DIR, Chunk, open_collection, read_pdf_chunks

BATCH = 256


def collect() -> list[Chunk]:
    pdfs = sorted(DOCTRINE_DIR.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {DOCTRINE_DIR}. Put doctrine PDFs there first.")
    chunks: list[Chunk] = []
    for pdf in pdfs:
        t0 = time.time()
        these = read_pdf_chunks(pdf)
        pages = {c.page for c in these}
        print(f"  {these[0].pub if these else pdf.stem:12} {len(these):5} chunks from {len(pages):4} pages  ({time.time()-t0:4.1f}s)  {pdf.name}")
        chunks.extend(these)
    return chunks


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="read and chunk the PDFs, write nothing")
    args = ap.parse_args()

    print(f"Reading PDFs from {DOCTRINE_DIR}")
    chunks = collect()
    print(f"Total: {len(chunks)} chunks")
    if args.check:
        return

    print(f"Writing index to {INDEX_DIR} (first run downloads the embedding model, about 80 MB)")
    col = open_collection(create=True)
    t0 = time.time()
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i + BATCH]
        col.add(
            ids=[c.chunk_id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[{"pub": c.pub, "title": c.title, "file": c.file, "page": c.page} for c in batch],
        )
        done = min(i + BATCH, len(chunks))
        print(f"  embedded {done}/{len(chunks)}  ({time.time()-t0:5.0f}s)", end="\r")
    print()
    print(f"Done. {col.count()} chunks in collection '{col.name}'. Next: python ask.py --retrieve-only \"your question\"")


if __name__ == "__main__":
    main()
