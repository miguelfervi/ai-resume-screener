"""FastAPI dependencies and shared request helpers."""

from __future__ import annotations

from functools import lru_cache

from ..config import Settings, get_settings


@lru_cache
def get_cached_settings() -> Settings:
    """Cached settings for FastAPI Depends (separate from config.get_settings)."""
    return get_settings()


def index_ready(settings: Settings) -> bool:
    """True when ChromaDB has an indexed collection with documents."""
    chroma_dir = settings.chroma_dir
    if not chroma_dir.is_dir():
        return False
    # ignore placeholder files like .gitkeep
    has_data = any(p.name != ".gitkeep" and not p.name.startswith(".") for p in chroma_dir.iterdir())
    if not has_data:
        return False
    try:
        from ..rag.store import ChromaStore

        return ChromaStore(chroma_dir).count() > 0
    except Exception:
        return False
