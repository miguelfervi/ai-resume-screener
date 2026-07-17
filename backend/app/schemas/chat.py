"""Chat and health API schemas.

Keep in sync with frontend/src/types/api.ts (camelCase serialization aliases).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..config import CHAT_MODELS


class ChatMessage(BaseModel):
    role: str = Field(description="user or assistant")
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)
    model: str | None = Field(
        default=None,
        description="Optional Gemini chat model id from the allowlist",
    )

    @field_validator("model")
    @classmethod
    def validate_chat_model(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        model = value.strip()
        if model not in CHAT_MODELS:
            allowed = ", ".join(CHAT_MODELS)
            raise ValueError(f"Unsupported model '{model}'. Allowed: {allowed}")
        return model


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
    model: str = ""
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


def metrics_to_response(metrics_dict: dict[str, Any]) -> RunMetricsResponse:
    """Build API metrics from RunMetrics.to_dict() output."""
    return RunMetricsResponse.model_validate(metrics_dict)
