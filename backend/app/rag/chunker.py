from __future__ import annotations

import re

from ..invariants import check_chunk_metadata, check_chunks_non_empty
from ..schemas import DocumentChunk

# Approximate tokens ≈ chars / 4 for English/Spanish CV text
_CHARS_PER_TOKEN = 4

_SECTION_HEADING_RE = re.compile(
    r"^(?:#{1,3}\s+)?(?:\*\*)?("
    r"Summary|Experience|Education|Skills|Languages|Projects|Certifications|Contact|"
    r"Resumen|Experiencia|Formaci[oó]n|Habilidades|Idiomas|Proyectos|Certificaciones|Contacto"
    r")(?:\*\*)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_MD_HEADING_RE = re.compile(r"^#{1,3}\s+\**(.+?)\**\s*$", re.MULTILINE)


def chunk_document(
    text: str,
    *,
    candidate_name: str,
    source_file: str,
    chunk_size_tokens: int = 500,
    chunk_overlap_tokens: int = 50,
) -> list[DocumentChunk]:
    sections = _split_sections(text)
    max_chars = max(chunk_size_tokens, 80) * _CHARS_PER_TOKEN
    overlap_chars = max(chunk_overlap_tokens, 0) * _CHARS_PER_TOKEN

    chunks: list[DocumentChunk] = []
    index = 0
    for section, body in sections:
        pieces = _window(body, max_chars, overlap_chars)
        for piece in pieces:
            chunk = DocumentChunk(
                text=piece,
                candidate_name=candidate_name,
                source_file=source_file,
                section=section,
                chunk_index=index,
            )
            check_chunk_metadata(chunk)
            chunks.append(chunk)
            index += 1

    check_chunks_non_empty(chunks, source_file)
    return chunks


def _split_sections(text: str) -> list[tuple[str, str]]:
    cleaned = text.strip()
    if not cleaned:
        return [("Body", "")]

    matches = list(_SECTION_HEADING_RE.finditer(cleaned))
    if not matches:
        md = list(_MD_HEADING_RE.finditer(cleaned))
        if md:
            return _sections_from_matches(cleaned, md, title_group=1)
        return [("Body", cleaned)]

    return _sections_from_matches(cleaned, matches, title_group=1)


def _sections_from_matches(
    text: str,
    matches: list[re.Match[str]],
    *,
    title_group: int,
) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("Header", preamble))

    for i, match in enumerate(matches):
        title = re.sub(r"[*#]", "", match.group(title_group)).strip().title()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((title, body))
    return sections or [("Body", text.strip())]


def _window(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            # prefer break on paragraph/sentence
            cut = text.rfind("\n", start + max_chars // 2, end)
            if cut <= start:
                cut = text.rfind(". ", start + max_chars // 2, end)
            if cut > start:
                end = cut + 1
        piece = text[start:end].strip()
        if piece:
            parts.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)
    return parts
