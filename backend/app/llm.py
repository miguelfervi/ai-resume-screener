"""LLM factory — Google Gemini chat and embeddings.

Isolates the rest of the codebase from the concrete provider so tests can
mock at the factory boundary.
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from .config import Settings, get_settings


class LLMUnavailableError(RuntimeError):
    """Raised when Gemini cannot be instantiated (missing API key)."""


def _require_api_key(settings: Settings) -> str:
    if not settings.google_api_key:
        raise LLMUnavailableError(
            "GOOGLE_API_KEY is not set. Add it to backend/.env to use Gemini."
        )
    return settings.google_api_key


def build_chat_model(settings: Settings | None = None) -> BaseChatModel:
    """Return a LangChain chat model backed by Google Gemini."""
    settings = settings or get_settings()
    api_key = _require_api_key(settings)

    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=api_key,
        temperature=settings.llm_temperature,
    )


def build_embeddings(settings: Settings | None = None) -> Embeddings:
    """Return a LangChain embeddings model backed by Google text-embedding-004."""
    settings = settings or get_settings()
    api_key = _require_api_key(settings)

    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embedding_model,
        google_api_key=api_key,
    )
