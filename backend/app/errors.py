"""Shared helpers for mapping provider failures to API responses."""

from __future__ import annotations

QUOTA_DETAIL = (
    "Gemini quota exceeded (free tier). Wait a minute and try again, "
    "or enable billing on your Google AI Studio key."
)


def is_quota_error(exc: BaseException) -> bool:
    """True when Gemini / Google APIs signal rate limit or exhausted quota."""
    msg = str(exc).lower()
    markers = (
        "429",
        "resourceexhausted",
        "resource exhausted",
        "quota",
        "rate limit",
        "ratelimit",
        "too many requests",
    )
    return any(m in msg for m in markers)
