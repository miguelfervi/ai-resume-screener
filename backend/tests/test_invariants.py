from __future__ import annotations

import pytest

from app.invariants import (
    InvariantError,
    check,
    check_answer_grounded,
    check_chunk_metadata,
    check_chunks_non_empty,
    check_index_populated,
    check_retrieval_has_evidence,
    check_sources_from_retrieved,
    check_unique_slugs,
)
from tests.conftest import make_chunk, make_retrieved, make_source


def test_check_passes() -> None:
    check(True, "ok")


def test_check_raises() -> None:
    with pytest.raises(InvariantError, match="must fail"):
        check(False, "must fail")


def test_chunk_metadata_and_non_empty() -> None:
    chunk = make_chunk()
    check_chunk_metadata(chunk)
    check_chunks_non_empty([chunk], "jane-doe.pdf")


def test_chunks_non_empty_fails() -> None:
    with pytest.raises(InvariantError):
        check_chunks_non_empty([], "empty.pdf")


def test_index_populated() -> None:
    check_index_populated(3, min_docs=1)
    with pytest.raises(InvariantError):
        check_index_populated(0, min_docs=1)


def test_retrieval_has_evidence() -> None:
    chunks = [make_retrieved(score=0.7), make_retrieved(score=0.4)]
    check_retrieval_has_evidence(chunks, min_score=0.65)
    with pytest.raises(InvariantError):
        check_retrieval_has_evidence([make_retrieved(score=0.2)], min_score=0.65)


def test_sources_from_retrieved() -> None:
    chunk = make_retrieved()
    source = make_source()
    check_sources_from_retrieved([source], [chunk])
    bad = make_source(section="Education")
    with pytest.raises(InvariantError):
        check_sources_from_retrieved([bad], [chunk])


def test_answer_grounded() -> None:
    check_answer_grounded("Jane Doe knows Python.", [make_retrieved()], is_no_evidence_case=False)
    check_answer_grounded("No evidence.", [], is_no_evidence_case=True)


def test_unique_slugs() -> None:
    check_unique_slugs(["a", "b"])
    with pytest.raises(InvariantError):
        check_unique_slugs(["a", "a"])
