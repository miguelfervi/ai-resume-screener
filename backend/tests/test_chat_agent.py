from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

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
        "cors_origins": ["http://localhost:5173"],
    }
    base.update(kwargs)
    return Settings(_env_file=None, **base)


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
    response = SimpleNamespace(
        content="Jane Doe has strong Python skills.",
        usage_metadata={"input_tokens": 10, "output_tokens": 5},
    )
    invoke_result = SimpleNamespace(response=response, model="gemini-flash-latest")
    state = {
        "question": "Who knows Python?",
        "history": [],
        "context_ok": True,
        "retrieved": [make_retrieved().model_dump()],
        "metrics": {},
    }
    with patch(
        "app.agents.chat_agent.invoke_chat_with_fallback",
        return_value=invoke_result,
    ) as mocked:
        out = generate_answer(state, settings)
    assert "Jane Doe" in out["answer"]
    assert out["metrics"]["model"] == "gemini-flash-latest"
    assert out["metrics"]["input_tokens"] == 10
    mocked.assert_called_once()
    prompt = mocked.call_args.args[0]
    assert "skill-matching" in prompt
    assert "short list" in prompt
    assert "full profiles" in prompt


def test_generate_answer_profile_prompt_keeps_detail() -> None:
    settings = _settings()
    response = SimpleNamespace(
        content="Jane Doe is a backend engineer in Madrid.",
        usage_metadata={},
    )
    invoke_result = SimpleNamespace(response=response, model="gemini-flash-latest")
    state = {
        "question": "Summarize the profile of Jane Doe",
        "history": [],
        "context_ok": True,
        "retrieved": [make_retrieved().model_dump()],
        "metrics": {},
    }
    with patch(
        "app.agents.chat_agent.invoke_chat_with_fallback",
        return_value=invoke_result,
    ) as mocked:
        generate_answer(state, settings)
    prompt = mocked.call_args.args[0]
    assert "profile or summarize" in prompt
    assert "skill-matching" not in prompt


def test_generate_answer_passes_selected_model() -> None:
    settings = _settings()
    response = SimpleNamespace(content="ok", usage_metadata={})
    invoke_result = SimpleNamespace(response=response, model="gemini-flash-lite-latest")
    state = {
        "question": "Who knows Python?",
        "history": [],
        "model": "gemini-flash-lite-latest",
        "context_ok": True,
        "retrieved": [make_retrieved().model_dump()],
        "metrics": {},
    }
    with patch(
        "app.agents.chat_agent.invoke_chat_with_fallback",
        return_value=invoke_result,
    ) as mocked:
        out = generate_answer(state, settings)
    assert out["metrics"]["model"] == "gemini-flash-lite-latest"
    assert mocked.call_args.kwargs["model"] == "gemini-flash-lite-latest"


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


def test_cite_sources_one_chip_per_candidate() -> None:
    chunks = [
        make_retrieved(
            candidate_name="Emma Wright",
            section="Skills",
            score=0.92,
            text="React TypeScript",
        ).model_dump(),
        make_retrieved(
            candidate_name="Emma Wright",
            section="Experience",
            score=0.90,
            text="React at Pixel Labs",
        ).model_dump(),
        make_retrieved(
            candidate_name="Emma Wright",
            section="Projects",
            score=0.91,
            text="React dashboard",
        ).model_dump(),
        make_retrieved(
            candidate_name="Lucía Fernández",
            source_file="lucia-fernandez.pdf",
            section="Habilidades",
            score=0.89,
            text="React",
        ).model_dump(),
    ]
    out = cite_sources(
        {
            "context_ok": True,
            "answer": "Emma Wright and Lucía Fernández have React experience.",
            "retrieved": chunks,
            "metrics": {},
        }
    )
    assert len(out["sources"]) == 2
    by_name = {s["candidate_name"]: s for s in out["sources"]}
    assert by_name["Emma Wright"]["section"] == "Skills"
    assert by_name["Emma Wright"]["score"] == 0.92
    assert by_name["Lucía Fernández"]["section"] == "Habilidades"


def test_cite_sources_empty_when_no_context() -> None:
    out = cite_sources({"context_ok": False, "retrieved": [], "metrics": {}})
    assert out["sources"] == []
