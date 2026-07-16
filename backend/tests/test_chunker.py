from __future__ import annotations

from app.rag.chunker import chunk_document
from tests.conftest import SAMPLE_CV_MD


def test_chunk_by_section_metadata() -> None:
    chunks = chunk_document(
        SAMPLE_CV_MD,
        candidate_name="Jane Doe",
        source_file="jane-doe.pdf",
    )
    assert chunks
    sections = {c.section for c in chunks}
    assert "Skills" in sections or "Summary" in sections
    for c in chunks:
        assert c.candidate_name == "Jane Doe"
        assert c.source_file == "jane-doe.pdf"
        assert c.text.strip()
        assert c.chunk_index >= 0


def test_chunk_indices_are_sequential() -> None:
    chunks = chunk_document(
        SAMPLE_CV_MD,
        candidate_name="Jane Doe",
        source_file="jane-doe.pdf",
    )
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_spanish_section_headings() -> None:
    text = """# Ana Torres

## Habilidades
Python · Django

## Formación
**Grado** — UPC (2018)
"""
    chunks = chunk_document(
        text,
        candidate_name="Ana Torres",
        source_file="ana-torres.pdf",
    )
    sections = {c.section for c in chunks}
    assert "Habilidades" in sections or "Formación" in sections
