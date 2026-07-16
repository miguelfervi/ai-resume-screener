"""PDF text extraction for the ingest pipeline."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pymupdf
import pymupdf4llm

from .invariants import check_extracted_text

logger = logging.getLogger("resume_screener.extractors")

SUPPORTED_EXTENSIONS = {".pdf"}

_WHITESPACE_RE = re.compile(r"[ \t]+")


class UnsupportedFileError(ValueError):
    """Raised when the file type is not supported."""


class ExtractionError(ValueError):
    """Raised when PDF text extraction fails."""


def extract_text_from_path(path: str | Path) -> str:
    """Extract structured Markdown text from a PDF file on disk."""
    pdf_path = Path(path)
    if not pdf_path.is_file():
        raise ExtractionError(f"PDF not found: {path}")
    if pdf_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileError(
            f"Unsupported file type '{pdf_path.suffix}'. Supported: {SUPPORTED_EXTENSIONS}"
        )

    try:
        with pymupdf.open(pdf_path) as doc:
            markdown = pymupdf4llm.to_markdown(doc)
    except Exception as exc:
        raise ExtractionError(f"Failed to extract text from {pdf_path.name}") from exc

    text = _normalize(markdown) if markdown and markdown.strip() else ""
    check_extracted_text(text, pdf_path.name)
    return text


def extract_text_from_bytes(content: bytes, filename: str = "document.pdf") -> str:
    """Extract text from PDF bytes (useful in tests)."""
    try:
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            markdown = pymupdf4llm.to_markdown(doc)
    except Exception as exc:
        raise ExtractionError(f"Failed to extract text from {filename}") from exc

    text = _normalize(markdown) if markdown and markdown.strip() else ""
    check_extracted_text(text, filename)
    return text


def _normalize(text: str) -> str:
    """Collapse horizontal whitespace; preserve paragraph breaks."""
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)
