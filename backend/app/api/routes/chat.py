from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_cached_settings, index_ready
from ...agents.chat_agent import run_chat
from ...config import Settings
from ...errors import QUOTA_DETAIL, is_quota_error
from ...schemas import ChatRequest, ChatResponse, Source, metrics_to_response

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_cached_settings),
) -> ChatResponse:
    if not index_ready(settings):
        raise HTTPException(
            status_code=503,
            detail="Vector index is empty. Run scripts/ingest.py first.",
        )

    history = [{"role": m.role, "content": m.content} for m in body.history]
    try:
        result = run_chat(
            body.question,
            history,
            model=body.model,
            settings=settings,
        )
    except Exception as exc:
        if is_quota_error(exc):
            raise HTTPException(status_code=429, detail=QUOTA_DETAIL) from exc
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    sources = [Source.model_validate(s) for s in result.get("sources") or []]
    metrics = metrics_to_response(result.get("metrics") or {})
    return ChatResponse(
        answer=result.get("answer") or "",
        sources=sources,
        metrics=metrics,
    )
