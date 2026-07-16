"""Health check route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_cached_settings, index_ready
from ...config import Settings
from ...schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_cached_settings)) -> HealthResponse:
    return HealthResponse(status="ok", index_ready=index_ready(settings))
