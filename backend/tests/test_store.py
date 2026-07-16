from __future__ import annotations

from pathlib import Path

from app.rag.store import ChromaStore, distance_to_score
from tests.conftest import FakeEmbeddings, make_chunk


def test_distance_to_score_cosine() -> None:
    assert distance_to_score(0.0) == 1.0
    assert distance_to_score(0.35) == 0.65
    assert distance_to_score(1.5) == 0.0


def test_store_add_query_count(tmp_chroma: Path, fake_embeddings: FakeEmbeddings) -> None:
    store = ChromaStore(tmp_chroma, embeddings=fake_embeddings)
    assert store.count() == 0

    n = store.add_chunks(
        [
            make_chunk(text="Python FastAPI backend", section="Skills", chunk_index=0),
            make_chunk(
                text="UPC computer science degree",
                section="Education",
                chunk_index=1,
            ),
        ]
    )
    assert n == 2
    assert store.count() == 2

    hits = store.query("Python FastAPI", top_k=2, min_score=0.0)
    assert hits
    assert any("Python" in h.text for h in hits)


def test_store_filter_by_candidate(tmp_chroma: Path, fake_embeddings: FakeEmbeddings) -> None:
    store = ChromaStore(tmp_chroma, embeddings=fake_embeddings)
    store.add_chunks(
        [
            make_chunk(candidate_name="Jane Doe", text="Jane Python skills"),
            make_chunk(
                candidate_name="Tom Wilson",
                source_file="tom-wilson.pdf",
                text="Tom AWS cloud",
                section="Skills",
                chunk_index=1,
            ),
        ]
    )
    hits = store.query("skills", top_k=5, min_score=0.0, candidate_name="Jane Doe")
    assert hits
    assert all(h.candidate_name == "Jane Doe" for h in hits)


def test_store_reset(tmp_chroma: Path, fake_embeddings: FakeEmbeddings) -> None:
    store = ChromaStore(tmp_chroma, embeddings=fake_embeddings)
    store.add_chunks([make_chunk()])
    assert store.count() == 1
    store.reset()
    assert store.count() == 0
