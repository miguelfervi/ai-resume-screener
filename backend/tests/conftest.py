"""Shared test helpers — no network, no real Gemini."""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import pytest

from app.schemas import DocumentChunk, RetrievedChunk, Source


class FakeEmbeddings:
    """Token-bag embeddings so overlapping text scores high in Chroma.

    Important demo tokens get fixed high-weight dimensions so name/skill
    queries clear the retriever's score floors under cosine distance.
    """

    _ANCHORS = {
        "jane": 0,
        "doe": 1,
        "python": 2,
        "fastapi": 3,
        "upc": 4,
        "tom": 5,
        "wilson": 6,
        "aws": 7,
    }

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"[a-z0-9]+", text.casefold())
        for tok in tokens:
            if tok in self._ANCHORS:
                vec[self._ANCHORS[tok]] += 8.0
            digest = hashlib.md5(tok.encode("utf-8")).digest()
            idx = 8 + (digest[0] % (self.dim - 8))
            vec[idx] += 0.35 + (digest[1] / 255.0) * 0.2
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


@pytest.fixture
def fake_embeddings() -> FakeEmbeddings:
    return FakeEmbeddings()


@pytest.fixture
def tmp_chroma(tmp_path: Path) -> Path:
    return tmp_path / "chroma"


def make_chunk(
    *,
    text: str = "Python and FastAPI experience",
    candidate_name: str = "Jane Doe",
    source_file: str = "jane-doe.pdf",
    section: str = "Skills",
    chunk_index: int = 0,
) -> DocumentChunk:
    return DocumentChunk(
        text=text,
        candidate_name=candidate_name,
        source_file=source_file,
        section=section,
        chunk_index=chunk_index,
    )


def make_retrieved(
    *,
    text: str = "Python and FastAPI experience",
    candidate_name: str = "Jane Doe",
    source_file: str = "jane-doe.pdf",
    section: str = "Skills",
    score: float = 0.9,
) -> RetrievedChunk:
    snippet = text if len(text) <= 220 else text[:217] + "..."
    return RetrievedChunk(
        text=text,
        candidate_name=candidate_name,
        source_file=source_file,
        section=section,
        score=score,
        snippet=snippet,
    )


def make_source(
    *,
    candidate_name: str = "Jane Doe",
    file: str = "jane-doe.pdf",
    section: str = "Skills",
    snippet: str = "Python",
    score: float = 0.9,
) -> Source:
    return Source(
        candidate_name=candidate_name,
        file=file,
        section=section,
        snippet=snippet,
        score=score,
    )


SAMPLE_CV_MD = """# Jane Doe
Senior Backend Engineer

## Summary
Jane builds APIs with Python and FastAPI.

## Skills
Python · FastAPI · PostgreSQL · AWS

## Education
**MSc Computer Science** — Universitat Politècnica de Catalunya (UPC) (2016)

## Experience
**Senior Backend Engineer** — TechFlow (2020 – Present)
- Led Python services
"""
