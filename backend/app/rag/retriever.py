from __future__ import annotations

import re

from ..schemas import RetrievedChunk
from .store import ChromaStore

_NAME_MATCH_FLOOR = 0.42
_BOOST_FLOOR = 0.48
_SECTION_BOOST = 0.08
_SKILL_BOOST = 0.10
_ROLE_BOOST = 0.09

_PDF_RE = re.compile(r"\b([a-z0-9][a-z0-9._-]{2,}\.pdf)\b", re.IGNORECASE)
_SLUG_RE = re.compile(r"\b([a-z][a-z0-9]+(?:-[a-z0-9]+)+)\b", re.IGNORECASE)

_SKILL_TERMS = (
    "python",
    "fastapi",
    "django",
    "flask",
    "react",
    "next.js",
    "nextjs",
    "typescript",
    "javascript",
    "node.js",
    "nodejs",
    "java",
    "kotlin",
    "swift",
    "ios",
    "android",
    "aws",
    "gcp",
    "azure",
    "docker",
    "kubernetes",
    "k8s",
    "postgresql",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    "graphql",
    "terraform",
    "pytest",
    "figma",
    "css",
    "html",
    "golang",
    "rust",
    "spark",
    "kafka",
    "airflow",
)

_GO_RE = re.compile(r"\bgo\b", re.I)

_ROLE_PATTERNS: list[tuple[re.Pattern[str], tuple[str, ...]]] = [
    (
        re.compile(
            r"\b(frontend|front-end|front end|ui developer|react developer|"
            r"desarrollador(?:a)? front(?:end)?)\b",
            re.I,
        ),
        ("Header", "Experience", "Experiencia", "Skills", "Habilidades", "Projects", "Proyectos"),
    ),
    (
        re.compile(
            r"\b(backend|back-end|back end|server[- ]side|api developer|"
            r"desarrollador(?:a)? back(?:end)?)\b",
            re.I,
        ),
        ("Header", "Experience", "Experiencia", "Skills", "Habilidades", "Projects", "Proyectos"),
    ),
    (
        re.compile(
            r"\b(full[- ]?stack|fullstack|desarrollador(?:a)? full[- ]?stack)\b",
            re.I,
        ),
        ("Header", "Experience", "Experiencia", "Skills", "Habilidades", "Projects", "Proyectos"),
    ),
    (
        re.compile(
            r"\b(engineering manager|eng(?:ineering)? manager|\bem\b|people manager|"
            r"manager de ingenier[ií]a)\b",
            re.I,
        ),
        ("Header", "Experience", "Experiencia", "Summary", "Resumen", "Skills", "Habilidades"),
    ),
    (
        re.compile(
            r"\b(design(?:er)?|product design|ux|ui\/ux|diseñador(?:a)?)\b",
            re.I,
        ),
        ("Header", "Experience", "Experiencia", "Skills", "Habilidades", "Projects", "Proyectos"),
    ),
    (
        re.compile(
            r"\b(data (?:engineer|scientist)|ml engineer|machine learning|"
            r"ingenier[oó]a? de datos|cient[ií]fic[oa] de datos)\b",
            re.I,
        ),
        ("Header", "Experience", "Experiencia", "Skills", "Habilidades", "Projects", "Proyectos"),
    ),
    (
        re.compile(r"\b(devops|sre|platform engineer|ingenier[oó]a? de plataforma)\b", re.I),
        ("Header", "Experience", "Experiencia", "Skills", "Habilidades", "Projects", "Proyectos"),
    ),
    (
        re.compile(r"\b(ios|android|mobile|m[oó]vil)\b", re.I),
        ("Header", "Experience", "Experiencia", "Skills", "Habilidades", "Projects", "Proyectos"),
    ),
]

_INTENT_SECTIONS: list[tuple[re.Pattern[str], tuple[str, ...]]] = [
    (
        re.compile(
            r"\b(summar(?:y|ise|ize)|overview|profile|about|resumen|perfil|sobre)\b",
            re.I,
        ),
        ("Summary", "Resumen", "Header", "Experience", "Experiencia"),
    ),
    (
        re.compile(r"\b(certificat\w*|credentials?|certificacion(?:es)?)\b", re.I),
        ("Certifications", "Certificaciones"),
    ),
    (
        re.compile(r"\b(languages?|idiomas?|speaks?|habla)\b", re.I),
        ("Languages", "Idiomas"),
    ),
    (
        re.compile(
            r"\b(education|degree|university|universitat|universidad|college|"
            r"gradu\w*|egresad\w*|alumni|formaci[oó]n|estudi[oó])\b",
            re.I,
        ),
        ("Education", "Formación"),
    ),
    (
        re.compile(r"\b(project\w*|portfolio|proyectos?)\b", re.I),
        ("Projects", "Proyectos"),
    ),
    (
        re.compile(
            r"\b(experience|worked|role|job|career|experiencia|trabaj[oó]|puesto)\b",
            re.I,
        ),
        ("Experience", "Experiencia", "Header"),
    ),
    (
        re.compile(
            r"\b(skills?|stack|technologies|tecnolog[ií]as?|habilidades|tech)\b",
            re.I,
        ),
        ("Skills", "Habilidades"),
    ),
]

_SKILL_SECTIONS = ("Skills", "Habilidades", "Projects", "Proyectos", "Experience", "Experiencia")
_EDU_SECTIONS = ("Education", "Formación")
_ACRONYM_RE = re.compile(r"\b([A-Z]{2,6})\b")
_VAGUE_RE = re.compile(
    r"\b(someone|anybody|anyone|who|which|any|people|candidates?|"
    r"alguien|qui[eé]n|cu[aá]l(?:es)?|alg[uú]n|personas?|candidat[oa]s?)\b",
    re.I,
)


def match_candidate_names(question: str, names: list[str]) -> list[str]:
    q = question.casefold()
    matched: list[str] = []
    for name in sorted(names, key=len, reverse=True):
        if name.casefold() in q:
            matched.append(name)
    return matched


def match_source_files(question: str, known_files: set[str] | None = None) -> list[str]:
    files: list[str] = []
    for m in _PDF_RE.finditer(question):
        files.append(m.group(1).lower())
    for m in _SLUG_RE.finditer(question):
        slug = m.group(1).lower()
        if slug.endswith(".pdf"):
            continue
        files.append(f"{slug}.pdf")
    # de-dupe preserve order
    out: list[str] = []
    seen: set[str] = set()
    for f in files:
        if known_files is not None and f not in known_files:
            continue
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def detect_acronyms(question: str) -> list[str]:
    """Catch institution/tech acronyms like UPC, AWS, MIT (skip tiny words)."""
    skip = {"WHO", "WHAT", "WHICH", "FROM", "WITH", "HAVE", "DOES", "THE", "AND", "FOR", "CV", "PDF"}
    found: list[str] = []
    for m in _ACRONYM_RE.finditer(question):
        token = m.group(1)
        if token in skip or token in found:
            continue
        found.append(token)
    return found


def detect_institution_terms(question: str) -> list[str]:
    """Institution cues: acronyms (UPC/UGR) and place/university phrases."""
    terms = [a.casefold() for a in detect_acronyms(question)]
    q = question.casefold()
    places = (
        "granada",
        "barcelona",
        "madrid",
        "valencia",
        "sevilla",
        "bilbao",
        "london",
        "chicago",
        "upc",
        "ugr",
        "upf",
        "uab",
        "ub",
        "mit",
        "politècnica",
        "politecnica",
    )
    for p in places:
        if p in q and p not in terms:
            terms.append(p)
    for m in re.finditer(
        r"(?:universidad|university|universitat)\s+(?:de\s+|of\s+)?([a-záéíóúñ]{3,})",
        q,
        re.IGNORECASE,
    ):
        token = m.group(1).casefold()
        if token not in {"the", "de", "of", "la", "el"} and token not in terms:
            terms.append(token)
    return terms


def _chunk_mentions_terms(chunk: RetrievedChunk, terms: list[str]) -> bool:
    if not terms:
        return True
    text = chunk.text.casefold()
    return any(t in text for t in terms)


def detect_skills(question: str) -> list[str]:
    q = question.casefold()
    found: list[str] = []
    for term in sorted(_SKILL_TERMS, key=len, reverse=True):
        needle = term.strip()
        if needle in q and needle not in found:
            found.append(needle)
    if _GO_RE.search(question) and "go" not in found and "golang" not in found:
        found.append("go")
    return found


def preferred_sections(question: str) -> list[str]:
    sections: list[str] = []
    for pattern, secs in _INTENT_SECTIONS:
        if pattern.search(question):
            sections.extend(secs)
    for pattern, secs in _ROLE_PATTERNS:
        if pattern.search(question):
            sections.extend(secs)
    # unique preserve order
    out: list[str] = []
    seen: set[str] = set()
    for s in sections:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def matched_role_sections(question: str) -> list[str]:
    sections: list[str] = []
    for pattern, secs in _ROLE_PATTERNS:
        if pattern.search(question):
            sections.extend(secs)
    out: list[str] = []
    seen: set[str] = set()
    for s in sections:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def adaptive_floor(question: str, min_score: float) -> float:
    """Lower evidence floor for short/vague hiring questions."""
    tokens = re.findall(r"[a-z0-9+]{2,}", question.casefold())
    vague = bool(_VAGUE_RE.search(question)) or len(tokens) <= 5
    specific = bool(
        _PDF_RE.search(question)
        or detect_skills(question)
        or detect_institution_terms(question)
        or matched_role_sections(question)
        or any(p.search(question) for p, _ in _INTENT_SECTIONS)
    )
    if specific:
        return min_score
    if vague:
        return max(0.40, min_score - 0.12)
    if len(tokens) <= 8:
        return max(0.45, min_score - 0.08)
    return min_score


def _dedupe_merge(*groups: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    seen: set[tuple[str, str, str]] = set()
    merged: list[RetrievedChunk] = []
    for group in groups:
        for chunk in sorted(group, key=lambda c: c.score, reverse=True):
            key = (chunk.source_file, chunk.section, chunk.text[:120])
            if key in seen:
                continue
            seen.add(key)
            merged.append(chunk)
    merged.sort(key=lambda c: c.score, reverse=True)
    return merged[:top_k]


def _promote(chunk: RetrievedChunk, pass_score: float, boost: float = 0.0) -> RetrievedChunk:
    chunk.score = round(min(1.0, max(chunk.score + boost, pass_score)), 4)
    return chunk


def _apply_soft_boosts(
    chunks: list[RetrievedChunk],
    *,
    question: str,
    skills: list[str],
    intent_sections: list[str],
    role_sections: list[str],
    floor: float,
    pass_score: float,
) -> list[RetrievedChunk]:
    active_role_patterns = [p for p, _ in _ROLE_PATTERNS if p.search(question)]
    out: list[RetrievedChunk] = []
    for chunk in chunks:
        if chunk.score < floor:
            out.append(chunk)
            continue
        boost = 0.0
        section = chunk.section
        text_l = chunk.text.casefold()

        if intent_sections and section in intent_sections:
            boost += _SECTION_BOOST
        if role_sections and section in role_sections:
            boost += _ROLE_BOOST * 0.5
            if any(p.search(chunk.text) for p in active_role_patterns):
                boost += _ROLE_BOOST * 0.5
        if skills and section in _SKILL_SECTIONS:
            hits = sum(1 for s in skills if s in text_l)
            if hits:
                boost += _SKILL_BOOST + 0.02 * min(hits, 3)

        if boost > 0:
            out.append(_promote(chunk, pass_score, boost))
        else:
            out.append(chunk)
    return out


def retrieve(
    store: ChromaStore,
    question: str,
    *,
    top_k: int = 6,
    min_score: float = 0.65,
) -> list[RetrievedChunk]:
    """Retrieve CV chunks with name/file/section/skill/role boosts."""
    pass_score = min_score if min_score > 0 else 0.65
    floor = adaptive_floor(question, pass_score)
    skills = detect_skills(question)
    acronyms = detect_acronyms(question)
    institutions = detect_institution_terms(question)
    intent_sections = preferred_sections(question)
    role_sections = matched_role_sections(question)
    section_targets = list(dict.fromkeys([*intent_sections, *role_sections]))
    if institutions and not any(s in _EDU_SECTIONS for s in section_targets):
        section_targets = list(dict.fromkeys([*_EDU_SECTIONS, *section_targets]))

    fetch_k = max(top_k * 3, 12)
    general = store.query(question, top_k=fetch_k, min_score=0.0)

    focused: list[RetrievedChunk] = []

    for name in match_candidate_names(question, store.candidate_names()):
        hits = store.query(
            question,
            top_k=top_k,
            min_score=0.0,
            candidate_name=name,
            sections=section_targets or None,
        )
        usable = [h for h in hits if h.score >= _NAME_MATCH_FLOOR]
        if not usable and section_targets:
            # Named + intent section can score low but is still the right evidence.
            usable = [h for h in hits if h.score >= 0.28]
        if not usable:
            hits = store.query(
                question,
                top_k=top_k,
                min_score=0.0,
                candidate_name=name,
            )
            usable = [h for h in hits if h.score >= _NAME_MATCH_FLOOR]
        for hit in usable:
            focused.append(_promote(hit, pass_score))

    known_files: set[str] = set()
    try:
        meta = store.collection.get(include=["metadatas"])
        known_files = {
            str(m.get("source_file", "")).lower()
            for m in (meta.get("metadatas") or [])
            if m and m.get("source_file")
        }
    except Exception:
        known_files = set()

    for source_file in match_source_files(question, known_files or None):
        hits = store.query(
            question,
            top_k=top_k,
            min_score=0.0,
            source_file=source_file,
            sections=section_targets or None,
        )
        if not hits and section_targets:
            hits = store.query(question, top_k=top_k, min_score=0.0, source_file=source_file)
        for hit in hits:
            if hit.score >= _NAME_MATCH_FLOOR:
                focused.append(_promote(hit, pass_score))

    if section_targets:
        hits = store.query(
            question,
            top_k=top_k,
            min_score=0.0,
            sections=section_targets,
        )
        for hit in hits:
            if hit.score < _BOOST_FLOOR:
                continue
            # Institution questions must mention the school/place in the chunk.
            if institutions and hit.section in _EDU_SECTIONS:
                if not _chunk_mentions_terms(hit, institutions):
                    continue
            focused.append(_promote(hit, pass_score, _SECTION_BOOST))

    if skills:
        hits = store.query(
            question,
            top_k=top_k,
            min_score=0.0,
            sections=list(_SKILL_SECTIONS),
        )
        for hit in hits:
            text_l = hit.text.casefold()
            if hit.score >= _BOOST_FLOOR and any(s in text_l for s in skills):
                focused.append(_promote(hit, pass_score, _SKILL_BOOST))

    if institutions:
        hits = store.query(
            question,
            top_k=max(top_k, 10),
            min_score=0.0,
            sections=list(_EDU_SECTIONS),
        )
        for hit in hits:
            if hit.score >= 0.28 and _chunk_mentions_terms(hit, institutions):
                focused.append(_promote(hit, pass_score, _SECTION_BOOST))

    boosted_general = _apply_soft_boosts(
        general,
        question=question,
        skills=skills,
        intent_sections=intent_sections,
        role_sections=role_sections,
        floor=floor,
        pass_score=pass_score,
    )
    if institutions:
        boosted_general = [
            c
            for c in boosted_general
            if c.section not in _EDU_SECTIONS or _chunk_mentions_terms(c, institutions)
        ]

    return _dedupe_merge(focused, boosted_general, top_k=top_k)
