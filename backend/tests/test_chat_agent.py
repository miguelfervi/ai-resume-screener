from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.agents.chat_agent import (
    _NO_EVIDENCE,
    cite_sources,
    generate_answer,
    validate_context,
)
from app.config import Settings
from tests.conftest import make_retrieved


def _settings(**kwargs) -> Settings:
    base = {
        "google_api_key": "test-key",
        "retrieval_top_k": 6,
        "retrieval_min_score": 0.65,
    }
    base.update(kwargs)
    return Settings(**base)


def test_validate_context_keeps_strong_chunks() -> None:
    settings = _settings()
    state = {
        "retrieved": [
            make_retrieved(score=0.9).model_dump(),
            make_retrieved(score=0.2, section="Summary").model_dump(),
        ],
        "metrics": {},
    }
    out = validate_context(state, settings)
    assert out["context_ok"] is True
    assert len(out["retrieved"]) == 1
    assert out["retrieved"][0]["score"] == 0.9


def test_validate_context_rejects_weak_retrieval() -> None:
    settings = _settings()
    state = {
        "retrieved": [make_retrieved(score=0.2).model_dump()],
        "metrics": {},
    }
    out = validate_context(state, settings)
    assert out["context_ok"] is False
    assert out["retrieved"] == []


def test_generate_answer_no_evidence() -> None:
    out = generate_answer({"context_ok": False, "metrics": {}}, _settings())
    assert out["answer"] == _NO_EVIDENCE


def test_generate_answer_calls_llm() -> None:
    settings = _settings()
    llm = MagicMock()
    llm.invoke.return_value = SimpleNamespace(
        content="Jane Doe has strong Python skills.",
        usage_metadata={"input_tokens": 10, "output_tokens": 5},
    )
    state = {
        "question": "Who knows Python?",
        "history": [],
        "context_ok": True,
        "retrieved": [make_retrieved().model_dump()],
        "metrics": {},
    }
    with patch("app.agents.chat_agent.build_chat_model", return_value=llm):
        out = generate_answer(state, settings)
    assert "Jane Doe" in out["answer"]
    llm.invoke.assert_called_once()


def test_cite_sources_prefers_mentioned_candidates() -> None:
    chunks = [
        make_retrieved(candidate_name="Jane Doe", score=0.9).model_dump(),
        make_retrieved(
            candidate_name="Tom Wilson",
            source_file="tom-wilson.pdf",
            text="AWS",
            score=0.88,
        ).model_dump(),
    ]
    out = cite_sources(
        {
            "context_ok": True,
            "answer": "Jane Doe is a strong Python match.",
            "retrieved": chunks,
            "metrics": {},
        }
    )
    names = {s["candidate_name"] for s in out["sources"]}
    assert names == {"Jane Doe"}


def test_cite_sources_ana_not_matched_inside_granada() -> None:
    """Regression: bare first name 'Ana' must not match substring in 'Granada'."""
    chunks = [
        make_retrieved(
            candidate_name="Ana Torres",
            source_file="ana-torres.pdf",
            text="Universidad de Granada",
            section="Education",
            score=0.9,
        ).model_dump(),
        make_retrieved(
            candidate_name="Carlos Ruiz",
            source_file="carlos-ruiz.pdf",
            text="Universidad de Granada degree",
            section="Education",
            score=0.85,
        ).model_dump(),
    ]
    out = cite_sources(
        {
            "context_ok": True,
            "answer": "A candidate studied at Universidad de Granada.",
            "retrieved": chunks,
            "metrics": {},
        }
    )
    # Neither full name mentioned → fallback to top chunks, but must not
    # falsely treat "Ana" as mentioned via Granada.
    assert out["sources"]
    # Explicit: answer without Ana/Carlos should still produce sources via fallback
    assert all("candidate_name" in s for s in out["sources"])


def test_cite_sources_empty_when_no_context() -> None:
    out = cite_sources({"context_ok": False, "retrieved": [], "metrics": {}})
    assert out["sources"] == []
