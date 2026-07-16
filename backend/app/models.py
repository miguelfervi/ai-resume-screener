"""Pydantic models shared across agents and API.

Keep in sync with frontend/src/types/api.ts (camelCase serialization aliases).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Chat API
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str = Field(description="user or assistant")
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)


class Source(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    candidate_name: str = Field(serialization_alias="candidateName")
    file: str
    section: str
    snippet: str
    score: float


class RunMetricsResponse(BaseModel):
    """API-facing metrics (mirrors RunMetrics.to_dict)."""

    model_config = ConfigDict(populate_by_name=True)

    provider: str = "gemini"
    total_ms: float = Field(default=0.0, serialization_alias="totalMs")
    node_timings_ms: dict[str, float] = Field(
        default_factory=dict, serialization_alias="nodeTimingsMs"
    )
    input_tokens: int = Field(default=0, serialization_alias="inputTokens")
    output_tokens: int = Field(default=0, serialization_alias="outputTokens")
    chunks_retrieved: int = Field(default=0, serialization_alias="chunksRetrieved")
    sources_cited: int = Field(default=0, serialization_alias="sourcesCited")
    success: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    metrics: RunMetricsResponse


class HealthResponse(BaseModel):
    status: str
    index_ready: bool = Field(default=False, serialization_alias="indexReady")


# ---------------------------------------------------------------------------
# CV generation
# ---------------------------------------------------------------------------


class CandidateProfile(BaseModel):
    """Planned profile for offline CV generation."""

    slug: str
    full_name: str
    locale: str = "en"
    role_family: str = Field(description="e.g. backend, data, design")
    university: str | None = None
    seniority: str = "mid"


class GeneratedCV(BaseModel):
    slug: str
    full_name: str
    email: str
    pdf_path: str
    photo_path: str | None = None
    skills: list[str] = Field(default_factory=list)


class ManifestEntry(BaseModel):
    slug: str
    full_name: str
    email: str
    file: str
    skills: list[str] = Field(default_factory=list)
    locale: str = "en"


# ---------------------------------------------------------------------------
# RAG / ingest
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def metrics_to_response(metrics_dict: dict[str, Any]) -> RunMetricsResponse:
    """Build API metrics from RunMetrics.to_dict() output."""
    return RunMetricsResponse.model_validate(metrics_dict)
