"""Minimal PDF CV renderer using ReportLab — no browser, no LLM."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def render_cv_pdf(profile: dict[str, Any], output_path: Path) -> None:
    """Render a seed profile dict to a simple A4 PDF."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CVTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "CVSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=6,
    )
    section_style = ParagraphStyle(
        "CVSection",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "CVBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#333333"),
    )

    story: list[Any] = []
    full_name = _esc(profile["full_name"])
    story.append(Paragraph(full_name, title_style))

    if profile.get("headline"):
        story.append(Paragraph(_esc(profile["headline"]), subtitle_style))

    contact_parts = [profile.get("email", "")]
    if profile.get("location"):
        contact_parts.append(profile["location"])
    story.append(Paragraph(_esc(" · ".join(p for p in contact_parts if p)), body_style))
    story.append(Spacer(1, 6))

    if profile.get("summary"):
        story.append(Paragraph(_section_label(profile, "summary"), section_style))
        story.append(Paragraph(_esc(profile["summary"]), body_style))

    if profile.get("experience"):
        story.append(Paragraph(_section_label(profile, "experience"), section_style))
        for job in profile["experience"]:
            dates = f"{job.get('start', '')} – {job.get('end', 'Present')}"
            story.append(
                Paragraph(
                    f"<b>{_esc(job.get('title', ''))}</b> — {_esc(job.get('company', ''))} "
                    f"<font color='#5c5c7a'>({dates})</font>",
                    body_style,
                )
            )
            for bullet in job.get("bullets", []):
                story.append(Paragraph(f"• {_esc(bullet)}", body_style))
            story.append(Spacer(1, 4))

    if profile.get("education"):
        story.append(Paragraph(_section_label(profile, "education"), section_style))
        for edu in profile["education"]:
            story.append(
                Paragraph(
                    f"<b>{_esc(edu.get('degree', ''))}</b> — {_esc(edu.get('institution', ''))} "
                    f"({_esc(edu.get('year', ''))})",
                    body_style,
                )
            )

    if profile.get("skills"):
        story.append(Paragraph(_section_label(profile, "skills"), section_style))
        story.append(Paragraph(_esc(" · ".join(profile["skills"])), body_style))

    if profile.get("languages"):
        story.append(Paragraph(_section_label(profile, "languages"), section_style))
        story.append(Paragraph(_esc(" · ".join(profile["languages"])), body_style))

    doc.build(story)


def _section_label(profile: dict[str, Any], key: str) -> str:
    locale = profile.get("locale", "en")
    labels = {
        "en": {
            "summary": "Summary",
            "experience": "Experience",
            "education": "Education",
            "skills": "Skills",
            "languages": "Languages",
        },
        "es": {
            "summary": "Resumen",
            "experience": "Experiencia",
            "education": "Formación",
            "skills": "Habilidades",
            "languages": "Idiomas",
        },
    }
    return labels.get(locale, labels["en"]).get(key, key.title())


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
