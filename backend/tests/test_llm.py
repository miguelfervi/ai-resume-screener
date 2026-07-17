from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.llm import invoke_chat_with_fallback


def test_invoke_chat_falls_back_on_quota() -> None:
    settings = Settings(
        _env_file=None,
        google_api_key="test-key",
        gemini_model="gemini-flash-latest",
        gemini_fallback_model="gemini-flash-lite-latest",
        cors_origins=["http://localhost:5173"],
    )
    primary = MagicMock()
    primary.invoke.side_effect = RuntimeError("429 ResourceExhausted: quota exceeded")
    fallback = MagicMock()
    fallback.invoke.return_value = SimpleNamespace(content="ok from fallback")

    with patch(
        "app.llm.build_chat_model",
        side_effect=[primary, fallback],
    ) as builder:
        result = invoke_chat_with_fallback("hello", settings)

    assert result.response.content == "ok from fallback"
    assert result.model == "gemini-flash-lite-latest"
    assert builder.call_count == 2
    assert builder.call_args_list[0].kwargs["model"] == "gemini-flash-latest"
    assert builder.call_args_list[1].kwargs["model"] == "gemini-flash-lite-latest"


def test_invoke_chat_does_not_fallback_on_other_errors() -> None:
    settings = Settings(
        _env_file=None,
        google_api_key="test-key",
        gemini_model="gemini-flash-latest",
        gemini_fallback_model="gemini-flash-lite-latest",
        cors_origins=["http://localhost:5173"],
    )
    primary = MagicMock()
    primary.invoke.side_effect = RuntimeError("500 internal")

    with patch("app.llm.build_chat_model", return_value=primary) as builder:
        raised = False
        try:
            invoke_chat_with_fallback("hello", settings)
        except RuntimeError as exc:
            raised = True
            assert "500" in str(exc)

    assert raised
    assert builder.call_count == 1


def test_invoke_chat_uses_explicit_model() -> None:
    settings = Settings(
        _env_file=None,
        google_api_key="test-key",
        gemini_model="gemini-flash-latest",
        gemini_fallback_model="gemini-flash-lite-latest",
        cors_origins=["http://localhost:5173"],
    )
    primary = MagicMock()
    primary.invoke.return_value = SimpleNamespace(content="ok")

    with patch("app.llm.build_chat_model", return_value=primary) as builder:
        result = invoke_chat_with_fallback(
            "hello",
            settings,
            model="gemini-flash-lite-latest",
        )

    assert result.model == "gemini-flash-lite-latest"
    assert builder.call_args.kwargs["model"] == "gemini-flash-lite-latest"


def test_invoke_chat_does_not_fallback_when_model_explicit() -> None:
    settings = Settings(
        _env_file=None,
        google_api_key="test-key",
        gemini_model="gemini-flash-latest",
        gemini_fallback_model="gemini-flash-lite-latest",
        cors_origins=["http://localhost:5173"],
    )
    primary = MagicMock()
    primary.invoke.side_effect = RuntimeError("429 ResourceExhausted: quota exceeded")

    with patch("app.llm.build_chat_model", return_value=primary) as builder:
        raised = False
        try:
            invoke_chat_with_fallback(
                "hello",
                settings,
                model="gemini-flash-latest",
            )
        except RuntimeError as exc:
            raised = True
            assert "429" in str(exc)

    assert raised
    assert builder.call_count == 1
