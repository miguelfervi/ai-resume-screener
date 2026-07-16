"""Runtime invariant checks for the CV screener pipeline.

These are explicit, named guards that encode assumptions the pipeline relies on.
Failing an invariant indicates a programming error, so they raise ``InvariantError``
— a subclass of ``AssertionError`` — with a clear description.

Usage in production code:
    check(condition, "description of what must be true")
    check_extracted_text(text, filename)

Usage in tests: import and call directly — they raise on failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import DocumentChunk, ManifestEntry, RetrievedChunk, Source


class InvariantError(AssertionError):
    """Raised when a pipeline invariant is violated."""


def check(condition: bool, message: str) -> None:
    """Assert that *condition* is truthy; raise ``InvariantError`` if not."""
    if not condition:
        raise InvariantError(f"Invariant violated: {message}")


# ---------------------------------------------------------------------------
# Generic guards
# ---------------------------------------------------------------------------


def check_extracted_text(text: str, filename: str) -> None:
    """Text extraction must produce a non-empty string for a valid PDF."""
    check(isinstance(text, str), "extracted text must be a str")
    check(
        len(text.strip()) > 0,
        f"extracted text must be non-empty for '{filename}'",
    )


def check_token_counts(input_tokens: int, output_tokens: int) -> None:
    """Token counts reported by the LLM must be non-negative."""
    check(input_tokens >= 0, f"input_tokens must be >= 0, got {input_tokens}")
    check(output_tokens >= 0, f"output_tokens must be >= 0, got {output_tokens}")


def check_answer_non_empty(answer: str, *, allow_empty: bool = False) -> None:
    """Chat answer must be non-empty unless explicitly allowed (no-evidence case)."""
    if allow_empty:
        return
    check(
        isinstance(answer, str) and len(answer.strip()) > 0,
        "chat answer must be non-empty",
    )


# ---------------------------------------------------------------------------
# CV generation
# ---------------------------------------------------------------------------


def check_pdf_exists(path: str | Path) -> None:
    """Generated PDF must exist and have content."""
    p = Path(path)
    check(p.is_file(), f"PDF must exist at {path}")
    check(p.stat().st_size > 0, f"PDF must be non-empty: {path}")


def check_manifest_entry(entry: "ManifestEntry") -> None:
    """Manifest entry must have minimum required fields."""
    check(len(entry.full_name.strip()) > 0, "manifest entry must have full_name")
    check(len(entry.email.strip()) > 0, "manifest entry must have email")
    check(len(entry.skills) > 0, f"manifest entry must have skills: {entry.slug}")
    check(len(entry.file.strip()) > 0, "manifest entry must reference a file")


def check_unique_slugs(slugs: list[str]) -> None:
    """CV slugs must be unique across the manifest."""
    check(len(slugs) == len(set(slugs)), f"duplicate slugs found: {slugs}")


# ---------------------------------------------------------------------------
# RAG ingest
# ---------------------------------------------------------------------------


def check_chunks_non_empty(chunks: list["DocumentChunk"], source_file: str) -> None:
    """Each indexed PDF must produce at least one chunk."""
    check(
        len(chunks) > 0,
        f"at least one chunk required for '{source_file}'",
    )


def check_chunk_metadata(chunk: "DocumentChunk") -> None:
    """Every chunk must carry candidate and source metadata."""
    check(len(chunk.candidate_name.strip()) > 0, "chunk must have candidate_name")
    check(len(chunk.source_file.strip()) > 0, "chunk must have source_file")
    check(len(chunk.section.strip()) > 0, "chunk must have section")


def check_index_populated(doc_count: int, min_docs: int = 1) -> None:
    """Vector index must contain a minimum number of documents."""
    check(
        doc_count >= min_docs,
        f"index must have at least {min_docs} documents, got {doc_count}",
    )


# ---------------------------------------------------------------------------
# Chat / retrieval
# ---------------------------------------------------------------------------


def check_retrieval_has_evidence(
    chunks: list["RetrievedChunk"],
    min_score: float,
    *,
    require_chunks: bool = True,
) -> None:
    """Retrieval must return chunks above the evidence threshold when required."""
    if not require_chunks:
        return
    check(len(chunks) > 0, "retrieval must return at least one chunk")
    max_score = max(c.score for c in chunks)
    check(
        max_score >= min_score,
        f"max retrieval score {max_score:.3f} below threshold {min_score}",
    )


def check_sources_from_retrieved(
    sources: list["Source"],
    chunks: list["RetrievedChunk"],
) -> None:
    """Every cited source must map to a retrieved chunk."""
    chunk_keys = {
        (c.candidate_name, c.source_file, c.section) for c in chunks
    }
    for src in sources:
        key = (src.candidate_name, src.file, src.section)
        check(
            key in chunk_keys,
            f"source {key!r} not found in retrieved chunks",
        )


def check_answer_grounded(
    answer: str,
    chunks: list["RetrievedChunk"],
    *,
    is_no_evidence_case: bool,
) -> None:
    """Grounded answers must reference real candidates when evidence exists."""
    if is_no_evidence_case:
        check_answer_non_empty(answer, allow_empty=False)
        return
    check(len(chunks) > 0, "grounded answer requires retrieved chunks")
    check_answer_non_empty(answer)
