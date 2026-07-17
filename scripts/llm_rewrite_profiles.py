#!/usr/bin/env python3
"""Rewrite CV narrative fields with Gemini (brief: LLM-generated texts).

Keeps facts (names, companies, dates, institutions, skills) and regenerates
summary, experience bullets, project descriptions, and education details.

Usage (repo root, backend venv + GOOGLE_API_KEY):
    python scripts/llm_rewrite_profiles.py              # all profiles
    python scripts/llm_rewrite_profiles.py --limit 3
    python scripts/llm_rewrite_profiles.py --slugs jane-doe,ana-torres
    python scripts/llm_rewrite_profiles.py --dry-run

Then regenerate PDFs:
    python scripts/generate_cvs.py --no-photos
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.errors import is_quota_error  # noqa: E402
from app.llm import invoke_chat_with_fallback  # noqa: E402

SEED = ROOT / "data" / "seed" / "profiles.json"


def _extract_json(text: str) -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"No JSON object in model response: {raw[:200]!r}")
    return json.loads(raw[start : end + 1])


def _prompt_for(profile: dict) -> str:
    locale = profile.get("locale", "en")
    lang = "Spanish" if locale == "es" else "English"
    payload = {
        "full_name": profile.get("full_name"),
        "headline": profile.get("headline"),
        "location": profile.get("location"),
        "skills": profile.get("skills", []),
        "summary": profile.get("summary"),
        "experience": profile.get("experience", []),
        "education": profile.get("education", []),
        "projects": profile.get("projects", []),
    }
    return f"""You rewrite resume narrative text for a recruiting demo.

Language for ALL rewritten fields: {lang}.
Keep facts unchanged: person name, job titles, companies, locations, date ranges,
degrees, institutions, years, skill names, project names.
Do NOT invent employers, degrees, or skills that are not in the input.
Make bullets concrete and varied (impact, scope, tools) — avoid repeating the same phrase.
Keep summary to 2–3 sentences. Each job: 3–4 bullets. Each project: 1 short description.
Education details: one short sentence each.

Return ONLY valid JSON with this shape:
{{
  "summary": "...",
  "experience": [{{"bullets": ["...", "..."]}}],
  "education": [{{"details": "..."}}],
  "projects": [{{"description": "..."}}]
}}
experience/education/projects arrays MUST match the input length and order.

INPUT:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def rewrite_profile(profile: dict, *, pause_sec: float) -> tuple[dict, str]:
    out = deepcopy(profile)
    result = invoke_chat_with_fallback(_prompt_for(profile))
    content = getattr(result.response, "content", None) or str(result.response)
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    data = _extract_json(str(content))

    if isinstance(data.get("summary"), str) and data["summary"].strip():
        out["summary"] = data["summary"].strip()

    exp_in = out.get("experience") or []
    exp_out = data.get("experience") or []
    if isinstance(exp_out, list) and len(exp_out) == len(exp_in):
        for job, rewritten in zip(exp_in, exp_out):
            bullets = rewritten.get("bullets") if isinstance(rewritten, dict) else None
            if isinstance(bullets, list) and bullets:
                job["bullets"] = [str(b).strip() for b in bullets if str(b).strip()][:5]

    edu_in = out.get("education") or []
    edu_out = data.get("education") or []
    if isinstance(edu_out, list) and len(edu_out) == len(edu_in):
        for edu, rewritten in zip(edu_in, edu_out):
            details = rewritten.get("details") if isinstance(rewritten, dict) else None
            if isinstance(details, str) and details.strip():
                edu["details"] = details.strip()

    proj_in = out.get("projects") or []
    proj_out = data.get("projects") or []
    if isinstance(proj_out, list) and len(proj_out) == len(proj_in):
        for proj, rewritten in zip(proj_in, proj_out):
            desc = rewritten.get("description") if isinstance(rewritten, dict) else None
            if isinstance(desc, str) and desc.strip():
                proj["description"] = desc.strip()

    out["llm_rewritten"] = True
    if pause_sec > 0:
        time.sleep(pause_sec)
    return out, result.model


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite CV texts with Gemini")
    parser.add_argument("--limit", type=int, default=0, help="Max profiles (0 = all)")
    parser.add_argument("--slugs", type=str, default="", help="Comma-separated slugs")
    parser.add_argument("--pause", type=float, default=2.0, help="Seconds between calls")
    parser.add_argument("--dry-run", action="store_true", help="Do not write profiles.json")
    args = parser.parse_args()

    # Avoid polluted shell CORS_ORIGINS breaking Settings JSON parse.
    os.environ.pop("CORS_ORIGINS", None)
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.google_api_key:
        print("GOOGLE_API_KEY missing in backend/.env", file=sys.stderr)
        return 1

    profiles: list[dict] = json.loads(SEED.read_text(encoding="utf-8"))
    wanted = {s.strip() for s in args.slugs.split(",") if s.strip()}
    indices = list(range(len(profiles)))
    if wanted:
        indices = [i for i, p in enumerate(profiles) if p.get("slug") in wanted]
    if args.limit > 0:
        indices = indices[: args.limit]

    print(
        f"Rewriting {len(indices)}/{len(profiles)} profiles "
        f"(primary={settings.gemini_model}, fallback={settings.gemini_fallback_model})"
    )

    updated = deepcopy(profiles)
    ok = 0
    for n, idx in enumerate(indices, start=1):
        slug = profiles[idx].get("slug", f"#{idx}")
        try:
            rewritten, model = rewrite_profile(profiles[idx], pause_sec=args.pause)
            updated[idx] = rewritten
            print(f"[{n}/{len(indices)}] OK  {slug}  ({model})")
            ok += 1
        except Exception as exc:  # noqa: BLE001 — continue remaining profiles
            kind = "quota" if is_quota_error(exc) else type(exc).__name__
            print(f"[{n}/{len(indices)}] FAIL {slug}: {kind}: {exc}", file=sys.stderr)
            if is_quota_error(exc):
                print("Stopping early due to quota.", file=sys.stderr)
                break

    if args.dry_run:
        print(f"Dry-run done ({ok} rewritten). No file written.")
        return 0 if ok else 1

    SEED.write_text(
        json.dumps(updated, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {SEED} ({ok} profiles rewritten with LLM).")
    print("Next: python scripts/generate_cvs.py --no-photos")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
