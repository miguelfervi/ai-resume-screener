"""Serve CV PDF files from the local data/cvs directory."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..deps import get_cached_settings
from ...config import Settings

router = APIRouter(prefix="/api", tags=["cvs"])


def _resolve_cv_path(filename: str, cvs_dir: Path) -> Path:
    """Resolve a CV PDF path, rejecting traversal and non-PDF names."""
    name = Path(filename).name
    if name != filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid CV filename.")
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    cvs_dir = cvs_dir.resolve()
    path = (cvs_dir / name).resolve()
    try:
        path.relative_to(cvs_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid CV path.") from exc

    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"CV '{name}' not found.")
    return path


@router.get("/cvs/{filename}")
def get_cv(
    filename: str,
    settings: Settings = Depends(get_cached_settings),
) -> FileResponse:
    path = _resolve_cv_path(filename, settings.cvs_dir)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
        content_disposition_type="inline",
    )
