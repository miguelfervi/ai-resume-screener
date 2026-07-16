from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..deps import get_cached_settings
from ...agents.ingest_agent import run_ingest
from ...config import Settings

router = APIRouter(prefix="/api", tags=["reindex"])


class ReindexResponse(BaseModel):
    status: str = "ok"
    doc_count: int = Field(serialization_alias="docCount")
    stored_count: int = Field(serialization_alias="storedCount")


@router.post("/reindex", response_model=ReindexResponse)
def reindex(settings: Settings = Depends(get_cached_settings)) -> ReindexResponse:
    if not settings.google_api_key:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_API_KEY is required to rebuild the index.",
        )
    try:
        result = run_ingest(reset=True, settings=settings)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ReindexResponse(
        status="ok",
        doc_count=int(result.get("doc_count") or 0),
        stored_count=int(result.get("stored_count") or 0),
    )
