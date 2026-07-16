from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render_cv_pdf(
    profile: dict[str, Any],
    output_path: Path,
    *,
    photo_path: Path | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CVTitle",
        parent=styles["Heading1"],
        fontSize=17,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        "CVSubtitle",
        parent=styles["Normal"],
        fontSize=10.5,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=4,
    )
    section_style = ParagraphStyle(
        "CVSection",
        parent=styles["Heading2"],
        fontSize=10.5,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=8,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "CVBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333"),
    )
    muted_style = ParagraphStyle(
        "CVMuted",
        parent=body_style,
        textColor=colors.HexColor("#5c5c7a"),
        fontSize=8.5,
    )

    story: list[Any] = []
    story.append(_build_header(profile, title_style, subtitle_style, body_style, photo_path))
    story.append(Spacer(1, 6))

    if profile.get("summary"):
        story.append(Paragraph(_section_label(profile, "summary"), section_style))
        story.append(Paragraph(_esc(profile["summary"]), body_style))

    if profile.get("experience"):
        story.append(Paragraph(_section_label(profile, "experience"), section_style))
        for job in profile["experience"]:
            dates = f"{job.get('start', '')} – {job.get('end', 'Present')}"
            loc = job.get("location")
            loc_bit = f" · {_esc(loc)}" if loc else ""
            story.append(
                Paragraph(
                    f"<b>{_esc(job.get('title', ''))}</b> — {_esc(job.get('company', ''))}"
                    f"<font color='#5c5c7a'> ({dates}{loc_bit})</font>",
                    body_style,
                )
            )
            for bullet in job.get("bullets", []):
                story.append(Paragraph(f"• {_esc(bullet)}", body_style))
            story.append(Spacer(1, 3))

    if profile.get("projects"):
        story.append(Paragraph(_section_label(profile, "projects"), section_style))
        for proj in profile["projects"]:
            story.append(
                Paragraph(
                    f"<b>{_esc(proj.get('name', ''))}</b> — {_esc(proj.get('description', ''))}",
                    body_style,
                )
            )

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
            if edu.get("details"):
                story.append(Paragraph(_esc(edu["details"]), muted_style))

    if profile.get("skills"):
        story.append(Paragraph(_section_label(profile, "skills"), section_style))
        story.append(Paragraph(_esc(" · ".join(profile["skills"])), body_style))

    if profile.get("certifications"):
        story.append(Paragraph(_section_label(profile, "certifications"), section_style))
        story.append(Paragraph(_esc(" · ".join(profile["certifications"])), body_style))

    if profile.get("languages"):
        story.append(Paragraph(_section_label(profile, "languages"), section_style))
        story.append(Paragraph(_esc(" · ".join(profile["languages"])), body_style))

    doc.build(story)


def _build_header(
    profile: dict[str, Any],
    title_style: ParagraphStyle,
    subtitle_style: ParagraphStyle,
    body_style: ParagraphStyle,
    photo_path: Path | None,
) -> Any:
    full_name = _esc(profile["full_name"])
    text_bits: list[Any] = [Paragraph(full_name, title_style)]

    if profile.get("headline"):
        text_bits.append(Paragraph(_esc(profile["headline"]), subtitle_style))

    contact_parts = [profile.get("email", "")]
    if profile.get("phone"):
        contact_parts.append(profile["phone"])
    if profile.get("location"):
        contact_parts.append(profile["location"])
    if profile.get("linkedin"):
        contact_parts.append(profile["linkedin"])
    text_bits.append(Paragraph(_esc(" · ".join(p for p in contact_parts if p)), body_style))

    if photo_path and photo_path.exists():
        photo = Image(str(photo_path), width=28 * mm, height=28 * mm)
        table = Table([[photo, text_bits]], colWidths=[32 * mm, None])
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 8),
                    ("RIGHTPADDING", (1, 0), (1, 0), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return table

    return KeepTogether(text_bits)


def _section_label(profile: dict[str, Any], key: str) -> str:
    locale = profile.get("locale", "en")
    labels = {
        "en": {
            "summary": "Summary",
            "experience": "Experience",
            "education": "Education",
            "skills": "Skills",
            "languages": "Languages",
            "projects": "Projects",
            "certifications": "Certifications",
        },
        "es": {
            "summary": "Resumen",
            "experience": "Experiencia",
            "education": "Formación",
            "skills": "Habilidades",
            "languages": "Idiomas",
            "projects": "Proyectos",
            "certifications": "Certificaciones",
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
