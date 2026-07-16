from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    FrameBreak,
    HRFlowable,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TEMPLATES = ("classic", "sidebar", "banner", "minimal", "coral")


@dataclass(frozen=True)
class Theme:
    name: str
    accent: str
    ink: str
    muted: str
    rule: str
    sidebar_bg: str = "#1e293b"
    sidebar_fg: str = "#e2e8f0"
    banner_bg: str = "#0f766e"
    banner_fg: str = "#f8fafc"


THEMES: dict[str, Theme] = {
    "classic": Theme(
        name="classic",
        accent="#2563eb",
        ink="#1a1a2e",
        muted="#5c5c7a",
        rule="#dbe3f0",
    ),
    "sidebar": Theme(
        name="sidebar",
        accent="#38bdf8",
        ink="#0f172a",
        muted="#64748b",
        rule="#e2e8f0",
        sidebar_bg="#0f172a",
        sidebar_fg="#e2e8f0",
    ),
    "banner": Theme(
        name="banner",
        accent="#0f766e",
        ink="#134e4a",
        muted="#5b6b6a",
        rule="#ccfbf1",
        banner_bg="#0f766e",
        banner_fg="#f0fdfa",
    ),
    "minimal": Theme(
        name="minimal",
        accent="#171717",
        ink="#171717",
        muted="#737373",
        rule="#d4d4d4",
    ),
    "coral": Theme(
        name="coral",
        accent="#b91c1c",
        ink="#1c1917",
        muted="#78716c",
        rule="#fecaca",
        banner_bg="#7f1d1d",
        banner_fg="#fef2f2",
    ),
}


def pick_template(profile: dict[str, Any]) -> str:
    explicit = profile.get("template")
    if explicit in TEMPLATES:
        return explicit
    digest = int(hashlib.md5(profile["slug"].encode()).hexdigest()[:8], 16)
    return TEMPLATES[digest % len(TEMPLATES)]


def render_cv_pdf(
    profile: dict[str, Any],
    output_path: Path,
    *,
    photo_path: Path | None = None,
) -> str:
    """Render CV PDF. Returns the template name used."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template = pick_template(profile)
    theme = THEMES[template]
    renderer: dict[str, Callable[..., None]] = {
        "classic": _render_classic,
        "sidebar": _render_sidebar,
        "banner": _render_banner,
        "minimal": _render_minimal,
        "coral": _render_coral,
    }
    renderer[template](profile, output_path, photo_path, theme)
    return template


def _styles(theme: Theme, prefix: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            f"{prefix}Title",
            parent=base["Heading1"],
            fontSize=18,
            textColor=colors.HexColor(theme.ink),
            spaceAfter=2,
            leading=22,
        ),
        "subtitle": ParagraphStyle(
            f"{prefix}Sub",
            parent=base["Normal"],
            fontSize=10.5,
            textColor=colors.HexColor(theme.accent),
            spaceAfter=4,
            leading=13,
        ),
        "section": ParagraphStyle(
            f"{prefix}Sec",
            parent=base["Heading2"],
            fontSize=10,
            textColor=colors.HexColor(theme.accent),
            spaceBefore=9,
            spaceAfter=3,
            leading=12,
        ),
        "body": ParagraphStyle(
            f"{prefix}Body",
            parent=base["Normal"],
            fontSize=8.8,
            leading=11.5,
            textColor=colors.HexColor(theme.ink),
        ),
        "muted": ParagraphStyle(
            f"{prefix}Muted",
            parent=base["Normal"],
            fontSize=8.2,
            leading=11,
            textColor=colors.HexColor(theme.muted),
        ),
        "side_title": ParagraphStyle(
            f"{prefix}SideTitle",
            parent=base["Normal"],
            fontSize=14,
            leading=17,
            textColor=colors.HexColor(theme.sidebar_fg),
            spaceAfter=4,
        ),
        "side_sub": ParagraphStyle(
            f"{prefix}SideSub",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor(theme.accent),
            spaceAfter=6,
        ),
        "side_label": ParagraphStyle(
            f"{prefix}SideLabel",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor(theme.accent),
            spaceBefore=8,
            spaceAfter=3,
        ),
        "side_body": ParagraphStyle(
            f"{prefix}SideBody",
            parent=base["Normal"],
            fontSize=7.8,
            leading=10.5,
            textColor=colors.HexColor(theme.sidebar_fg),
        ),
        "banner_title": ParagraphStyle(
            f"{prefix}BanTitle",
            parent=base["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor(theme.banner_fg),
            spaceAfter=2,
        ),
        "banner_sub": ParagraphStyle(
            f"{prefix}BanSub",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor(theme.banner_fg),
            spaceAfter=3,
        ),
        "banner_meta": ParagraphStyle(
            f"{prefix}BanMeta",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor(theme.banner_fg),
        ),
    }


def _render_classic(
    profile: dict[str, Any],
    output_path: Path,
    photo_path: Path | None,
    theme: Theme,
) -> None:
    s = _styles(theme, "classic")
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    story: list[Any] = [_header_row(profile, photo_path, s, theme)]
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor(theme.rule)))
    story.extend(_main_sections(profile, s, theme, with_skills=True, with_langs=True))
    doc.build(story)


def _render_minimal(
    profile: dict[str, Any],
    output_path: Path,
    photo_path: Path | None,
    theme: Theme,
) -> None:
    s = _styles(theme, "minimal")
    s["section"].textColor = colors.HexColor(theme.ink)
    s["section"].fontSize = 9
    s["section"].spaceBefore = 11
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    story: list[Any] = []
    story.append(Paragraph(_esc(profile["full_name"]), s["title"]))
    if profile.get("headline"):
        story.append(Paragraph(_esc(profile["headline"]), s["muted"]))
    story.append(Paragraph(_esc(_contact_line(profile)), s["muted"]))
    if photo_path and photo_path.exists():
        story.append(Spacer(1, 4))
        story.append(Image(str(photo_path), width=22 * mm, height=22 * mm))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(theme.ink)))
    story.extend(_main_sections(profile, s, theme, with_skills=True, with_langs=True, ruled=True))
    doc.build(story)


def _render_banner(
    profile: dict[str, Any],
    output_path: Path,
    photo_path: Path | None,
    theme: Theme,
) -> None:
    s = _styles(theme, "banner")
    page_w, page_h = A4
    banner_h = 40 * mm

    def on_page(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(theme.banner_bg))
        canvas.rect(0, page_h - banner_h, page_w, banner_h, fill=1, stroke=0)
        canvas.restoreState()

    doc = BaseDocTemplate(str(output_path), pagesize=A4)
    frame = Frame(
        16 * mm,
        12 * mm,
        page_w - 32 * mm,
        page_h - 12 * mm - 12 * mm,
        id="main",
    )
    doc.addPageTemplates([PageTemplate(id="Banner", frames=[frame], onPage=on_page)])

    header_bits: list[Any] = [Paragraph(_esc(profile["full_name"]), s["banner_title"])]
    if profile.get("headline"):
        header_bits.append(Paragraph(_esc(profile["headline"]), s["banner_sub"]))
    header_bits.append(Paragraph(_esc(_contact_line(profile)), s["banner_meta"]))

    if photo_path and photo_path.exists():
        photo = Image(str(photo_path), width=26 * mm, height=26 * mm)
        header = Table([[header_bits, photo]], colWidths=[135 * mm, 28 * mm])
        header.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
    else:
        header = KeepTogether(header_bits)

    # Pad so header sits inside the painted banner band
    story: list[Any] = [
        Spacer(1, 4 * mm),
        header,
        Spacer(1, 10 * mm),
    ]
    story.extend(_main_sections(profile, s, theme, with_skills=True, with_langs=True))
    doc.build(story)


def _render_coral(
    profile: dict[str, Any],
    output_path: Path,
    photo_path: Path | None,
    theme: Theme,
) -> None:
    s = _styles(theme, "coral")
    page_w, page_h = A4
    bar_w = 8 * mm

    def on_page(canvas: Any, _doc: Any) -> None:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(theme.accent))
        canvas.rect(0, 0, bar_w, page_h, fill=1, stroke=0)
        canvas.restoreState()

    doc = BaseDocTemplate(str(output_path), pagesize=A4)
    frame = Frame(
        bar_w + 12 * mm,
        12 * mm,
        page_w - bar_w - 24 * mm,
        page_h - 24 * mm,
        id="main",
    )
    doc.addPageTemplates([PageTemplate(id="Coral", frames=[frame], onPage=on_page)])

    story: list[Any] = [_header_row(profile, photo_path, s, theme)]
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor(theme.accent)))
    story.extend(_main_sections(profile, s, theme, with_skills=True, with_langs=True))
    doc.build(story)


def _render_sidebar(
    profile: dict[str, Any],
    output_path: Path,
    photo_path: Path | None,
    theme: Theme,
) -> None:
    s = _styles(theme, "sidebar")
    page_w, page_h = A4
    side_w = 58 * mm

    def on_page(canvas: Any, _doc: Any) -> None:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(theme.sidebar_bg))
        canvas.rect(0, 0, side_w, page_h, fill=1, stroke=0)
        canvas.restoreState()

    doc = BaseDocTemplate(str(output_path), pagesize=A4)
    side = Frame(6 * mm, 10 * mm, side_w - 12 * mm, page_h - 20 * mm, id="side")
    main = Frame(
        side_w + 8 * mm,
        10 * mm,
        page_w - side_w - 16 * mm,
        page_h - 20 * mm,
        id="main",
    )
    doc.addPageTemplates([PageTemplate(id="TwoCol", frames=[side, main], onPage=on_page)])

    side_story: list[Any] = []
    if photo_path and photo_path.exists():
        side_story.append(Image(str(photo_path), width=28 * mm, height=28 * mm))
        side_story.append(Spacer(1, 6))
    side_story.append(Paragraph(_esc(profile["full_name"]), s["side_title"]))
    if profile.get("headline"):
        side_story.append(Paragraph(_esc(profile["headline"]), s["side_sub"]))

    side_story.append(Paragraph(_section_label(profile, "contact"), s["side_label"]))
    for line in _contact_parts(profile):
        side_story.append(Paragraph(_esc(line), s["side_body"]))

    if profile.get("skills"):
        side_story.append(Paragraph(_section_label(profile, "skills"), s["side_label"]))
        for skill in profile["skills"]:
            side_story.append(Paragraph(f"• {_esc(skill)}", s["side_body"]))

    if profile.get("languages"):
        side_story.append(Paragraph(_section_label(profile, "languages"), s["side_label"]))
        side_story.append(Paragraph(_esc(" · ".join(profile["languages"])), s["side_body"]))

    if profile.get("certifications"):
        side_story.append(Paragraph(_section_label(profile, "certifications"), s["side_label"]))
        for cert in profile["certifications"]:
            side_story.append(Paragraph(f"• {_esc(cert)}", s["side_body"]))

    main_story = _main_sections(
        profile,
        s,
        theme,
        with_skills=False,
        with_langs=False,
        with_certs=False,
    )
    doc.build(side_story + [FrameBreak()] + main_story)


def _header_row(
    profile: dict[str, Any],
    photo_path: Path | None,
    s: dict[str, ParagraphStyle],
    theme: Theme,
) -> Any:
    bits: list[Any] = [Paragraph(_esc(profile["full_name"]), s["title"])]
    if profile.get("headline"):
        bits.append(Paragraph(_esc(profile["headline"]), s["subtitle"]))
    bits.append(Paragraph(_esc(_contact_line(profile)), s["muted"]))

    if photo_path and photo_path.exists():
        photo = Image(str(photo_path), width=28 * mm, height=28 * mm)
        table = Table([[photo, bits]], colWidths=[32 * mm, None])
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
    return KeepTogether(bits)


def _main_sections(
    profile: dict[str, Any],
    s: dict[str, ParagraphStyle],
    theme: Theme,
    *,
    with_skills: bool,
    with_langs: bool,
    with_certs: bool = True,
    ruled: bool = False,
) -> list[Any]:
    story: list[Any] = []

    def section(title_key: str) -> None:
        story.append(Paragraph(_section_label(profile, title_key), s["section"]))
        if ruled:
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=colors.HexColor(theme.rule),
                    spaceAfter=3,
                )
            )

    if profile.get("summary"):
        section("summary")
        story.append(Paragraph(_esc(profile["summary"]), s["body"]))

    if profile.get("experience"):
        section("experience")
        for job in profile["experience"]:
            dates = f"{job.get('start', '')} – {job.get('end', 'Present')}"
            loc = job.get("location")
            loc_bit = f" · {_esc(loc)}" if loc else ""
            story.append(
                Paragraph(
                    f"<b>{_esc(job.get('title', ''))}</b> — {_esc(job.get('company', ''))}"
                    f"<font color='{theme.muted}'> ({dates}{loc_bit})</font>",
                    s["body"],
                )
            )
            for bullet in job.get("bullets", []):
                story.append(Paragraph(f"• {_esc(bullet)}", s["body"]))
            story.append(Spacer(1, 2))

    if profile.get("projects"):
        section("projects")
        for proj in profile["projects"]:
            story.append(
                Paragraph(
                    f"<b>{_esc(proj.get('name', ''))}</b> — {_esc(proj.get('description', ''))}",
                    s["body"],
                )
            )

    if profile.get("education"):
        section("education")
        for edu in profile["education"]:
            story.append(
                Paragraph(
                    f"<b>{_esc(edu.get('degree', ''))}</b> — {_esc(edu.get('institution', ''))} "
                    f"({_esc(edu.get('year', ''))})",
                    s["body"],
                )
            )
            if edu.get("details"):
                story.append(Paragraph(_esc(edu["details"]), s["muted"]))

    if with_skills and profile.get("skills"):
        section("skills")
        story.append(Paragraph(_esc(" · ".join(profile["skills"])), s["body"]))

    if with_certs and profile.get("certifications"):
        section("certifications")
        story.append(Paragraph(_esc(" · ".join(profile["certifications"])), s["body"]))

    if with_langs and profile.get("languages"):
        section("languages")
        story.append(Paragraph(_esc(" · ".join(profile["languages"])), s["body"]))

    return story


def _contact_parts(profile: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    for key in ("email", "phone", "location", "linkedin"):
        val = profile.get(key)
        if val:
            parts.append(str(val))
    return parts


def _contact_line(profile: dict[str, Any]) -> str:
    return " · ".join(_contact_parts(profile))


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
            "contact": "Contact",
        },
        "es": {
            "summary": "Resumen",
            "experience": "Experiencia",
            "education": "Formación",
            "skills": "Habilidades",
            "languages": "Idiomas",
            "projects": "Proyectos",
            "certifications": "Certificaciones",
            "contact": "Contacto",
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
