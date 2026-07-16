from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_cached_settings
from app.config import Settings, get_settings
from app.main import app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    cvs_dir = tmp_path / "cvs"
    cvs_dir.mkdir()
    (cvs_dir / "jane-doe.pdf").write_bytes(b"%PDF-1.4\n%test\n")
    chroma = tmp_path / "chroma"
    chroma.mkdir()

    settings = Settings(
        google_api_key="test-key",
        chroma_path=str(chroma),
        cvs_path=str(cvs_dir),
    )

    get_settings.cache_clear()
    get_cached_settings.cache_clear()

    def _override() -> Settings:
        return settings

    app.dependency_overrides[get_cached_settings] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_cached_settings.cache_clear()


def test_health_ok(client: TestClient) -> None:
    with patch("app.api.routes.health.index_ready", return_value=True):
        res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["indexReady"] is True


def test_chat_requires_index(client: TestClient) -> None:
    with patch("app.api.routes.chat.index_ready", return_value=False):
        res = client.post("/api/chat", json={"question": "Who knows Python?", "history": []})
    assert res.status_code == 503


def test_chat_success(client: TestClient) -> None:
    fake_result = {
        "answer": "Jane Doe knows Python.",
        "sources": [
            {
                "candidate_name": "Jane Doe",
                "file": "jane-doe.pdf",
                "section": "Skills",
                "snippet": "Python",
                "score": 0.9,
            }
        ],
        "metrics": {
            "provider": "gemini",
            "model": "gemini-flash-latest",
            "total_ms": 12.0,
            "node_timings_ms": {},
            "input_tokens": 1,
            "output_tokens": 2,
            "chunks_retrieved": 1,
            "sources_cited": 1,
            "success": True,
        },
    }
    with (
        patch("app.api.routes.chat.index_ready", return_value=True),
        patch("app.api.routes.chat.run_chat", return_value=fake_result),
    ):
        res = client.post(
            "/api/chat",
            json={"question": "Who knows Python?", "history": []},
        )
    assert res.status_code == 200
    body = res.json()
    assert "Jane Doe" in body["answer"]
    assert body["sources"][0]["candidateName"] == "Jane Doe"
    assert body["metrics"]["success"] is True


def test_chat_maps_quota_to_429(client: TestClient) -> None:
    with (
        patch("app.api.routes.chat.index_ready", return_value=True),
        patch(
            "app.api.routes.chat.run_chat",
            side_effect=RuntimeError("429 ResourceExhausted: quota exceeded"),
        ),
    ):
        res = client.post(
            "/api/chat",
            json={"question": "Who knows Python?", "history": []},
        )
    assert res.status_code == 429
    assert "quota" in res.json()["detail"].lower()


def test_reindex_success(client: TestClient) -> None:
    with patch(
        "app.api.routes.reindex.run_ingest",
        return_value={"doc_count": 5, "stored_count": 12},
    ):
        res = client.post("/api/reindex")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["docCount"] == 5
    assert body["storedCount"] == 12


def test_get_cv_pdf(client: TestClient) -> None:
    res = client.get("/api/cvs/jane-doe.pdf")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/pdf")


def test_get_cv_rejects_invalid_names(client: TestClient) -> None:
    assert client.get("/api/cvs/readme.txt").status_code == 400
    # Backslash is rejected before filesystem lookup.
    assert client.get("/api/cvs/foo\\bar.pdf").status_code == 400
    assert client.get("/api/cvs/missing-candidate.pdf").status_code == 404
