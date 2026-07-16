"""Lightweight run metrics for observability per LangGraph node."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunMetrics:
    provider: str = "gemini"
    node_timings_ms: dict[str, float] = field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    chunks_retrieved: int = 0
    sources_cited: int = 0
    success: bool = False
    total_ms: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "total_ms": round(self.total_ms, 1),
            "node_timings_ms": {k: round(v, 1) for k, v in self.node_timings_ms.items()},
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "chunks_retrieved": self.chunks_retrieved,
            "sources_cited": self.sources_cited,
            "success": self.success,
        }


class Timer:
    """Context manager that records elapsed time into a metrics dict."""

    def __init__(self, sink: dict[str, float], key: str) -> None:
        self._sink = sink
        self._key = key
        self._start: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        elapsed_ms = (time.perf_counter() - self._start) * 1000
        self._sink[self._key] = self._sink.get(self._key, 0.0) + elapsed_ms
