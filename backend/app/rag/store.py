from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.api.types import EmbeddingFunction, Embeddings, Documents

from ..invariants import check_index_populated
from ..schemas import DocumentChunk, RetrievedChunk

COLLECTION_NAME = "cv_chunks"
# Free-tier Gemini embed quota is ~100 RPM; keep batches small.
_UPSERT_BATCH_SIZE = 40
_EMBED_MAX_RETRIES = 5


class _LangChainEmbeddingAdapter(EmbeddingFunction[Documents]):
    """Adapt LangChain Embeddings to Chroma's EmbeddingFunction protocol."""

    def __init__(self, embeddings: object) -> None:
        self._embeddings = embeddings

    def __call__(self, input: Documents) -> Embeddings:
        texts = list(input)
        delay = 40.0
        last_exc: Exception | None = None
        for attempt in range(_EMBED_MAX_RETRIES):
            try:
                return self._embeddings.embed_documents(texts)  # type: ignore[attr-defined]
            except Exception as exc:  # noqa: BLE001 — retry only on quota
                last_exc = exc
                msg = str(exc)
                if "429" not in msg and "ResourceExhausted" not in msg and "quota" not in msg.lower():
                    raise
                time.sleep(delay)
                delay = min(delay * 1.5, 120.0)
        assert last_exc is not None
        raise last_exc


class ChromaStore:
    def __init__(
        self,
        persist_dir: str | Path,
        *,
        embeddings: object | None = None,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._embeddings = embeddings
        kwargs: dict = {"name": collection_name}
        if embeddings is not None:
            kwargs["embedding_function"] = _LangChainEmbeddingAdapter(embeddings)
        self._collection: Collection = self._client.get_or_create_collection(**kwargs)

    @property
    def collection(self) -> Collection:
        return self._collection

    def count(self) -> int:
        return int(self._collection.count())

    def reset(self) -> None:
        name = self._collection.name
        self._client.delete_collection(name)
        kwargs: dict = {"name": name}
        if self._embeddings is not None:
            kwargs["embedding_function"] = _LangChainEmbeddingAdapter(self._embeddings)
        self._collection = self._client.get_or_create_collection(**kwargs)

    def add_chunks(self, chunks: Sequence[DocumentChunk]) -> int:
        if not chunks:
            return 0
        for start in range(0, len(chunks), _UPSERT_BATCH_SIZE):
            batch = chunks[start : start + _UPSERT_BATCH_SIZE]
            ids = [
                f"{c.source_file}::{c.section}::{c.chunk_index}"
                for c in batch
            ]
            documents = [c.text for c in batch]
            metadatas = [
                {
                    "candidate_name": c.candidate_name,
                    "source_file": c.source_file,
                    "section": c.section,
                    "chunk_index": c.chunk_index,
                }
                for c in batch
            ]
            self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            if start + _UPSERT_BATCH_SIZE < len(chunks):
                time.sleep(15)
        return len(chunks)

    def candidate_names(self) -> list[str]:
        if self.count() == 0:
            return []
        result = self._collection.get(include=["metadatas"])
        names = {
            str(meta.get("candidate_name", "")).strip()
            for meta in (result.get("metadatas") or [])
            if meta and meta.get("candidate_name")
        }
        return sorted(n for n in names if n)

    def query(
        self,
        question: str,
        *,
        top_k: int = 6,
        min_score: float = 0.0,
        candidate_name: str | None = None,
        source_file: str | None = None,
        sections: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        if self.count() == 0:
            return []

        where: dict | None = None
        clauses: list[dict] = []
        if candidate_name:
            clauses.append({"candidate_name": candidate_name})
        if source_file:
            clauses.append({"source_file": source_file})
        if sections:
            clauses.append({"section": {"$in": list(sections)}})
        if len(clauses) == 1:
            where = clauses[0]
        elif len(clauses) > 1:
            where = {"$and": clauses}

        kwargs: dict = {
            "query_texts": [question],
            "n_results": min(max(top_k, 1), max(self.count(), 1)),
            "include": ["documents", "metadatas", "distances"],
        }
        if where is not None:
            kwargs["where"] = where

        result = self._collection.query(**kwargs)
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        chunks: list[RetrievedChunk] = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            # Chroma cosine distance → similarity score in [0, 1]-ish
            score = max(0.0, 1.0 - float(dist))
            if score < min_score:
                continue
            text = doc or ""
            snippet = text if len(text) <= 220 else text[:217].rstrip() + "..."
            chunks.append(
                RetrievedChunk(
                    text=text,
                    candidate_name=str(meta.get("candidate_name", "")),
                    source_file=str(meta.get("source_file", "")),
                    section=str(meta.get("section", "")),
                    score=round(score, 4),
                    snippet=snippet,
                )
            )
        return chunks

    def verify(self, min_docs: int = 1) -> int:
        count = self.count()
        check_index_populated(count, min_docs=min_docs)
        return count
