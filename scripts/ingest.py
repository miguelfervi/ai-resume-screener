#!/usr/bin/env python3
"""Index CV PDFs into ChromaDB via the ingest LangGraph agent.

Usage (repo root, backend venv active, GOOGLE_API_KEY set):
    python scripts/ingest.py
    python scripts/ingest.py --no-reset
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.agents.ingest_agent import run_ingest  # noqa: E402
from app.config import get_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest CV PDFs into ChromaDB")
    parser.add_argument(
        "--cvs",
        type=Path,
        default=None,
        help="CV directory (default: settings.cvs_dir)",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not wipe the existing collection before indexing",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.google_api_key:
        print("GOOGLE_API_KEY is required. Set it in backend/.env")
        return 1

    result = run_ingest(
        cvs_dir=args.cvs,
        reset=not args.no_reset,
        settings=settings,
    )
    print(
        f"Indexed {result.get('stored_count')} chunks "
        f"→ {settings.chroma_dir} (docs={result.get('doc_count')})"
    )
    metrics = result.get("metrics") or {}
    print(f"Timings ms: {metrics.get('node_timings_ms')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
