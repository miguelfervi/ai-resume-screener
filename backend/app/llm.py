"""LLM factory — Google Gemini chat and embeddings.

Isolates the rest of the codebase from the concrete provider so tests can
mock at the factory boundary.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from .config import Settings, get_settings
from .errors import is_quota_error

logger = logging.getLogger("resume_screener.llm")


@dataclass(frozen=True)
class ChatInvokeResult:
    response: Any
    model: str


class LLMUnavailableError(RuntimeError):
    """Raised when Gemini cannot be instantiated (missing API key)."""


def _require_api_key(settings: Settings) -> str:
    if not settings.google_api_key:
        raise LLMUnavailableError(
            "GOOGLE_API_KEY is not set. Add it to backend/.env to use Gemini."
        )
    return settings.google_api_key


def build_chat_model(
    settings: Settings | None = None,
    *,
    model: str | None = None,
) -> BaseChatModel:
    """Return a LangChain chat model backed by Google Gemini."""
    settings = settings or get_settings()
    api_key = _require_api_key(settings)

    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model or settings.gemini_model,
        google_api_key=api_key,
        temperature=settings.llm_temperature,
    )


def invoke_chat_with_fallback(
    prompt: str,
    settings: Settings | None = None,
) -> ChatInvokeResult:
    """Invoke the primary Gemini model; on free-tier quota, retry fallback."""
    settings = settings or get_settings()
    primary = settings.gemini_model
    fallback = settings.gemini_fallback_model

    try:
        response = build_chat_model(settings, model=primary).invoke(prompt)
        return ChatInvokeResult(response=response, model=primary)
    except Exception as exc:
        if not is_quota_error(exc):
            raise
        if not fallback or fallback == primary:
            raise
        logger.warning(
            "Primary model %s hit quota (%s); falling back to %s",
            primary,
            type(exc).__name__,
            fallback,
        )
        response = build_chat_model(settings, model=fallback).invoke(prompt)
        return ChatInvokeResult(response=response, model=fallback)


def build_embeddings(settings: Settings | None = None) -> Embeddings:
    """Return a LangChain embeddings model (default: gemini-embedding-001)."""
    settings = settings or get_settings()
    api_key = _require_api_key(settings)

    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    model = settings.gemini_embedding_model
    if not model.startswith("models/"):
        model = f"models/{model}"

    return GoogleGenerativeAIEmbeddings(
        model=model,
        google_api_key=api_key,
    )
