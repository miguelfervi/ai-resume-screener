"""FastAPI dependencies and shared request helpers."""

from __future__ import annotations

from functools import lru_cache

from ..config import Settings, get_settings


@lru_cache
def get_cached_settings() -> Settings:
    """Cached settings for FastAPI Depends (separate from config.get_settings)."""
    return get_settings()


def index_ready(settings: Settings) -> bool:
    """True when ChromaDB collection directory exists and has persisted data."""
    chroma_dir = settings.chroma_dir
    if not chroma_dir.is_dir():
        return False
    return any(chroma_dir.iterdir())
