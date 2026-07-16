#!/usr/bin/env python3
"""Generate demo CV PDFs from seed profiles (+ AI headshots for a sample).

Usage (from repo root, backend venv active):
    python scripts/generate_cvs.py              # photos for SAMPLE_PHOTO_SLUGS only
    python scripts/generate_cvs.py --no-photos
    python scripts/generate_cvs.py --photos all
    python scripts/generate_cvs.py --force-photos
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.cv_renderer import pick_template, render_cv_pdf  # noqa: E402
from app.invariants import (  # noqa: E402
    check_manifest_entry,
    check_pdf_exists,
    check_unique_slugs,
)
from app.photo_generator import generate_cv_photo, photo_path_for  # noqa: E402
from app.schemas import ManifestEntry  # noqa: E402

DEFAULT_SEED = ROOT / "data" / "seed" / "profiles.json"
DEFAULT_OUT = ROOT / "data" / "cvs"
DEFAULT_PHOTOS = ROOT / "data" / "cvs" / "photos"

# Enough to show "AI photo on CV" without generating 30 images.
SAMPLE_PHOTO_SLUGS = (
    "jane-doe",
    "carlos-mendez",
    "emma-wright",
    "lucia-fernandez",
    "marcus-chen",
    "ana-torres",
)


def load_profiles(seed_path: Path) -> list[dict]:
    with seed_path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError(f"Seed file must be a non-empty JSON array: {seed_path}")
    return data


def build_manifest(
    profiles: list[dict],
    photo_files: dict[str, str],
    templates: dict[str, str],
) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []
    for profile in profiles:
        slug = profile["slug"]
        entry = ManifestEntry(
            slug=slug,
            full_name=profile["full_name"],
            email=profile["email"],
            file=f"{slug}.pdf",
            skills=profile.get("skills", []),
            locale=profile.get("locale", "en"),
            photo=photo_files.get(slug),
            template=templates.get(slug) or profile.get("template"),
        )
        check_manifest_entry(entry)
        entries.append(entry)
    check_unique_slugs([e.slug for e in entries])
    return entries


def photo_slugs_for_mode(mode: str, profiles: list[dict]) -> set[str]:
    if mode == "none":
        return set()
    if mode == "all":
        return {p["slug"] for p in profiles}
    return set(SAMPLE_PHOTO_SLUGS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate demo CV PDFs from seed data")
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--photos-dir", type=Path, default=DEFAULT_PHOTOS)
    parser.add_argument(
        "--photos",
        choices=("sample", "all", "none"),
        default="sample",
        help="sample=6 demo headshots (default), all=every CV, none=skip",
    )
    parser.add_argument("--no-photos", action="store_true", help="alias for --photos none")
    parser.add_argument("--force-photos", action="store_true")
    args = parser.parse_args()

    photo_mode = "none" if args.no_photos else args.photos
    profiles = load_profiles(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    wanted = photo_slugs_for_mode(photo_mode, profiles)

    photo_files: dict[str, str] = {}
    templates: dict[str, str] = {}

    for profile in profiles:
        slug = profile["slug"]
        photo: Path | None = None

        if "template" not in profile:
            profile["template"] = pick_template(profile)

        if slug in wanted:
            photo = photo_path_for(slug, args.photos_dir)
            print(f"  photo {slug}...")
            generate_cv_photo(profile, photo, force=args.force_photos)
            photo_files[slug] = f"photos/{slug}.jpg"

        pdf_path = args.out / f"{slug}.pdf"
        used = render_cv_pdf(profile, pdf_path, photo_path=photo)
        templates[slug] = used
        check_pdf_exists(pdf_path)
        print(f"  pdf {pdf_path.name} [{used}]")

    # persist template choices back into seed for reproducibility
    args.seed.write_text(
        json.dumps(profiles, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest_entries = build_manifest(profiles, photo_files, templates)
    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            [e.model_dump(exclude_none=True) for e in manifest_entries],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nGenerated {len(profiles)} PDFs → {args.out}")
    if photo_files:
        print(f"Photos → {args.photos_dir} ({len(photo_files)} of {len(profiles)})")
    print(f"Manifest → {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
