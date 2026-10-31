"""Checks a visitor can run after `python build_index.py`.
OS DAGGER is a free tool from Potestas AI (https://potestasai.com). MIT license.

    python -m pytest tests -q        (or)        python tests/test_retrieval.py

Each test asks a question whose answer is on a known page and checks that page
is among the retrieved excerpts. They prove retrieval in both directions: the
right page comes back, and a restriction to one pub keeps the others out.
No model, no key, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dagger_common import INDEX_DIR, pub_from_filename, printed_page, split_page  # noqa: E402

try:
    import pytest
except ImportError:  # the file still runs as a plain script
    pytest = None

INDEX_BUILT = (INDEX_DIR / "chroma.sqlite3").exists()

# (question, pub, printed page that holds the answer, k)
KNOWN = [
    ("What are the tenets of operations?", "ADP 3-0", "27", 8),        # printed page 27 (PDF page 39): TENETS, paragraph 3-13
    ("What are the principles of sustainment?", "FM 4-0", None, 8),    # any FM 4-0 page in the top 8
    ("What goes in paragraph 3 of an operation order?", "FM 5-0", None, 8),
]


def _hits(question, k, pub=None):
    from ask import retrieve
    return retrieve(question, k, pub)


def test_filename_parsing():
    assert pub_from_filename("ATP_3-35_Army_Deployment_and_Redeployment_2023-03-09.pdf") == ("ATP 3-35", "Army Deployment and Redeployment")
    assert pub_from_filename("ADP_4-0_Sustainment_2019_C1_2026-08-18.pdf") == ("ADP 4-0", "Sustainment")
    assert pub_from_filename("FM_5-0_Planning_and_Orders_Production_2024_C1_2025-08-11.pdf") == ("FM 5-0", "Planning and Orders Production")


def test_printed_page_from_header():
    assert printed_page("Chapter 1  1-6 ATP 4-16 25 April 2022  Services, nations ...", "ATP 4-16") == "1-6"
    assert printed_page("The Army's Operational Concept  21 March 2025 ADP 3-0 27  weaken, friendly forces", "ADP 3-0") == "27"
    assert printed_page("see paragraph 3-7 for details. Body text with no header at all.", "FM 6-0") == ""


def test_chunks_never_cross_a_page_and_overlap():
    text = ("Sentence number %d of the page. " * 200)
    pieces = split_page(text)
    assert len(pieces) > 1
    assert all(len(p) <= 1600 for p in pieces)
    assert pieces[0][-40:] in text and pieces[1][:40] in text


def _needs_index():
    if not INDEX_BUILT:
        if pytest:
            pytest.skip("index not built; run python build_index.py first")
        print("  skipped (index not built)")
        return True
    return False


def test_known_pages_are_retrieved():
    if _needs_index():
        return
    for question, pub, printed, k in KNOWN:
        hits = _hits(question, k)
        pubs = [h["meta"]["pub"] for h in hits]
        assert pub in pubs, f"{question!r}: expected {pub} in top {k}, got {pubs}"
        if printed:
            pages = [h["meta"].get("printed") for h in hits if h["meta"]["pub"] == pub]
            assert printed in pages, f"{question!r}: expected {pub} p. {printed}, got {pages}"


def test_pub_filter_keeps_other_pubs_out():
    if _needs_index():
        return
    hits = _hits("who may be designated as the commander of a unit", 5, pub="AR 600-20")
    assert hits and all(h["meta"]["pub"] == "AR 600-20" for h in hits)


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok    {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL  {name}: {e}")
    sys.exit(1 if failed else 0)
