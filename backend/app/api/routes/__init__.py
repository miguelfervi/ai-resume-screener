"""API route modules."""

from fastapi import APIRouter

from .chat import router as chat_router
from .health import router as health_router
from .reindex import router as reindex_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(reindex_router)
