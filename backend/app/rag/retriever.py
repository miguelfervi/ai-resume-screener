from __future__ import annotations

from .store import ChromaStore


def retrieve(
    store: ChromaStore,
    question: str,
    *,
    top_k: int = 6,
    min_score: float = 0.65,
):
    return store.query(question, top_k=top_k, min_score=min_score)
