"""RAG pipeline domain schemas."""

from __future__ import annotations

from pydantic import BaseModel


class DocumentChunk(BaseModel):
    text: str
    candidate_name: str
    source_file: str
    section: str
    chunk_index: int = 0


class RetrievedChunk(BaseModel):
    text: str
    candidate_name: str
    source_file: str
    section: str
    score: float
    snippet: str = ""
