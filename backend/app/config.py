"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Google Gemini
    google_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "text-embedding-004"
    llm_temperature: float = 0.0

    # Data paths (resolved relative to backend/)
    chroma_path: str = "../data/chroma"
    cvs_path: str = "../data/cvs"

    # RAG
    retrieval_top_k: int = 6
    retrieval_min_score: float = 0.65
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 50

    # API
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    def resolve_path(self, relative: str) -> Path:
        """Resolve a path relative to the backend directory."""
        return (_BACKEND_DIR / relative).resolve()

    @property
    def chroma_dir(self) -> Path:
        return self.resolve_path(self.chroma_path)

    @property
    def cvs_dir(self) -> Path:
        return self.resolve_path(self.cvs_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
