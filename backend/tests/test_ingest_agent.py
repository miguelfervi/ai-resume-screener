from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from app.agents.ingest_agent import (
    chunk_all,
    embed_and_store,
    extract_pdfs,
    load_manifest,
    run_ingest,
    verify_index,
)
from app.config import Settings
from tests.conftest import SAMPLE_CV_MD, FakeEmbeddings


def _settings(tmp_path: Path, cvs_dir: Path) -> Settings:
    return Settings(
        google_api_key="test-key",
        chroma_path=str(tmp_path / "chroma"),
        cvs_path=str(cvs_dir),
    )


def _write_fixture_cv(cvs_dir: Path) -> None:
    cvs_dir.mkdir(parents=True, exist_ok=True)
    pdf = cvs_dir / "jane-doe.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%fixture\n")
    manifest = [
        {
            "slug": "jane-doe",
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "file": "jane-doe.pdf",
            "skills": ["Python"],
        }
    ]
    (cvs_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_load_manifest_and_extract(tmp_path: Path) -> None:
    cvs_dir = tmp_path / "cvs"
    _write_fixture_cv(cvs_dir)

    state = load_manifest(
        {
            "cvs_dir": str(cvs_dir),
            "manifest_path": str(cvs_dir / "manifest.json"),
        }
    )
    assert state["pdf_paths"] == [str(cvs_dir / "jane-doe.pdf")]

    with patch(
        "app.agents.ingest_agent.extract_text_from_path",
        return_value=SAMPLE_CV_MD,
    ):
        extracted = extract_pdfs(
            {
                "cvs_dir": str(cvs_dir),
                "manifest_path": str(cvs_dir / "manifest.json"),
                "pdf_paths": state["pdf_paths"],
                "metrics": {},
            }
        )

    assert extracted["extracted"][0]["candidate_name"] == "Jane Doe"
    assert "Python" in extracted["extracted"][0]["text"]


def test_chunk_embed_verify_pipeline(tmp_path: Path, fake_embeddings: FakeEmbeddings) -> None:
    cvs_dir = tmp_path / "cvs"
    _write_fixture_cv(cvs_dir)
    settings = _settings(tmp_path, cvs_dir)

    chunked = chunk_all(
        {
            "extracted": [
                {
                    "text": SAMPLE_CV_MD,
                    "candidate_name": "Jane Doe",
                    "source_file": "jane-doe.pdf",
                }
            ],
            "metrics": {},
        },
        settings=settings,
    )
    assert chunked["chunks"]

    with patch("app.agents.ingest_agent.build_embeddings", return_value=fake_embeddings):
        stored = embed_and_store(
            {
                "chunks": chunked["chunks"],
                "reset": True,
                "metrics": {},
            },
            settings=settings,
        )
        assert stored["stored_count"] > 0

        verified = verify_index({"metrics": {}}, settings=settings)
        assert verified["doc_count"] > 0


def test_run_ingest_end_to_end(tmp_path: Path, fake_embeddings: FakeEmbeddings) -> None:
    cvs_dir = tmp_path / "cvs"
    _write_fixture_cv(cvs_dir)
    settings = _settings(tmp_path, cvs_dir)

    with (
        patch(
            "app.agents.ingest_agent.extract_text_from_path",
            return_value=SAMPLE_CV_MD,
        ),
        patch("app.agents.ingest_agent.build_embeddings", return_value=fake_embeddings),
    ):
        result = run_ingest(cvs_dir=cvs_dir, reset=True, settings=settings)

    assert result.get("doc_count", 0) > 0
    assert result.get("stored_count", 0) > 0
