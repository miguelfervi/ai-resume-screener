from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from .config import Settings, get_settings


def headshot_prompt(profile: dict[str, Any]) -> str:
    name = profile.get("full_name", "a professional")
    role = profile.get("headline", "software professional")
    location = profile.get("location", "")
    where = f" based in {location}" if location else ""
    return (
        f"Photorealistic LinkedIn-style professional headshot of {name}, "
        f"a {role}{where}. Neutral studio background, soft lighting, "
        f"business casual attire, facing camera, natural expression, "
        f"high quality portrait photo, no text, no watermark."
    )


def photo_path_for(slug: str, photos_dir: Path) -> Path:
    return photos_dir / f"{slug}.jpg"


def generate_cv_photo(
    profile: dict[str, Any],
    output_path: Path,
    *,
    settings: Settings | None = None,
    force: bool = False,
) -> Path:
    """Generate an AI headshot. Prefer Gemini; fall back to Pollinations."""
    settings = settings or get_settings()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        return output_path

    prompt = headshot_prompt(profile)

    if settings.google_api_key:
        try:
            _generate_with_gemini(prompt, output_path, settings)
            return output_path
        except Exception:
            # fall through to pollinations
            pass

    _generate_with_pollinations(prompt, output_path, seed_key=profile.get("slug", "cv"))
    return output_path


def _generate_with_gemini(prompt: str, output_path: Path, settings: Settings) -> None:
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.google_api_key)
    model = settings.gemini_image_model

    # Imagen path (generate_images) — preferred when model id starts with imagen
    if model.startswith("imagen"):
        response = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="1:1",
            ),
        )
        if not response.generated_images:
            raise RuntimeError("Gemini returned no images")
        image = response.generated_images[0].image
        output_path.write_bytes(image.image_bytes)
        return

    # Gemini native image models (e.g. gemini-2.5-flash-image)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    for part in response.parts:
        if part.inline_data is not None:
            output_path.write_bytes(part.inline_data.data)
            return
    raise RuntimeError(f"No image data from model {model}")


def _generate_with_pollinations(prompt: str, output_path: Path, *, seed_key: str) -> None:
    seed = int(hashlib.sha256(seed_key.encode()).hexdigest()[:8], 16) % 1_000_000
    url = (
        "https://image.pollinations.ai/prompt/"
        f"{quote(prompt)}"
        f"?width=512&height=512&seed={seed}&nologo=true&model=flux"
    )
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=90.0, follow_redirects=True) as client:
                res = client.get(url)
                res.raise_for_status()
                if not res.content or len(res.content) < 1000:
                    raise RuntimeError("empty/short image response")
                output_path.write_bytes(res.content)
                return
        except Exception as exc:
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"pollinations failed for {seed_key}: {last_err}")
