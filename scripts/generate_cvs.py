#!/usr/bin/env python3
"""Generate demo CV PDFs from seed profiles — no LLM, no browser.

Usage (from repo root):
    python scripts/generate_cvs.py
    python scripts/generate_cvs.py --seed data/seed/profiles.json --out data/cvs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.cv_renderer import render_cv_pdf  # noqa: E402
from app.invariants import (  # noqa: E402
    check_manifest_entry,
    check_pdf_exists,
    check_unique_slugs,
)
from app.schemas import ManifestEntry  # noqa: E402

DEFAULT_SEED = ROOT / "data" / "seed" / "profiles.json"
DEFAULT_OUT = ROOT / "data" / "cvs"


def load_profiles(seed_path: Path) -> list[dict]:
    with seed_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError(f"Seed file must be a non-empty JSON array: {seed_path}")
    return data


def build_manifest(profiles: list[dict], out_dir: Path) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []
    for profile in profiles:
        slug = profile["slug"]
        filename = f"{slug}.pdf"
        entry = ManifestEntry(
            slug=slug,
            full_name=profile["full_name"],
            email=profile["email"],
            file=filename,
            skills=profile.get("skills", []),
            locale=profile.get("locale", "en"),
        )
        check_manifest_entry(entry)
        entries.append(entry)
    check_unique_slugs([e.slug for e in entries])
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate demo CV PDFs from seed data")
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    profiles = load_profiles(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    for profile in profiles:
        pdf_path = args.out / f"{profile['slug']}.pdf"
        render_cv_pdf(profile, pdf_path)
        check_pdf_exists(pdf_path)
        print(f"  ✓ {pdf_path.name}")

    manifest_entries = build_manifest(profiles, args.out)
    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(
        json.dumps([e.model_dump() for e in manifest_entries], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nGenerated {len(profiles)} PDFs → {args.out}")
    print(f"Manifest → {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
