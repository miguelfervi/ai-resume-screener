from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from app.rag.retriever import (
    adaptive_floor,
    detect_institution_terms,
    detect_skills,
    match_candidate_names,
    preferred_sections,
    retrieve,
)
from app.schemas import RetrievedChunk
from tests.conftest import FakeEmbeddings, make_chunk
from app.rag.store import ChromaStore


def test_match_candidate_names() -> None:
    names = ["Jane Doe", "Ana Torres", "Tom Wilson"]
    assert match_candidate_names("Summarize Jane Doe", names) == ["Jane Doe"]
    assert match_candidate_names("anyone frontend", names) == []


def test_detect_skills_and_institutions() -> None:
    assert "python" in detect_skills("Who has Python and React?")
    assert "react" in detect_skills("Who has Python and React?")
    terms = detect_institution_terms("Which candidate graduated from UPC?")
    assert "upc" in terms


def test_spanish_intent_and_vague_cues() -> None:
    secs = preferred_sections("Resume el perfil de Jane Doe")
    assert "Resumen" in secs or "Summary" in secs
    assert "Skills" in secs or "Habilidades" in secs
    assert "Education" in secs or "Formación" in secs
    edu = preferred_sections("¿Quién se graduó de la UPC?")
    assert "Education" in edu or "Formación" in edu
    from app.rag.retriever import adaptive_floor

    assert adaptive_floor("¿Alguien del equipo?", 0.65) < 0.65


def test_preferred_sections_for_profile_summary() -> None:
    secs = preferred_sections("Summarize the profile of Jane Doe.")
    assert "Experience" in secs or "Experiencia" in secs
    assert "Skills" in secs or "Habilidades" in secs


def test_preferred_sections_for_education() -> None:
    secs = preferred_sections("Which candidate graduated from UPC?")
    assert "Education" in secs or "Formación" in secs


def test_adaptive_floor() -> None:
    assert adaptive_floor("React TypeScript", 0.65) == 0.65
    vague = adaptive_floor("someone", 0.65)
    assert vague < 0.65


def test_retrieve_top_k_and_name_boost(tmp_chroma: Path, fake_embeddings: FakeEmbeddings) -> None:
    store = ChromaStore(tmp_chroma, embeddings=fake_embeddings)
    store.add_chunks(
        [
            make_chunk(text="Jane Doe Python FastAPI skills", section="Skills"),
            make_chunk(
                text="Jane Doe UPC education degree",
                section="Education",
                chunk_index=1,
            ),
            make_chunk(
                candidate_name="Tom Wilson",
                source_file="tom-wilson.pdf",
                text="Tom AWS cloud architect",
                section="Skills",
                chunk_index=2,
            ),
        ]
    )
    hits = retrieve(store, "Summarize the profile of Jane Doe.", top_k=3, min_score=0.65)
    assert hits
    assert len(hits) <= 8  # profile queries may raise top_k
    assert any(h.candidate_name == "Jane Doe" for h in hits)
    # named boosts should clear the threshold
    assert any(h.score >= 0.65 and h.candidate_name == "Jane Doe" for h in hits)
    # Named profile summary should not be drowned by other candidates' headers.
    assert all(h.candidate_name == "Jane Doe" for h in hits)


def test_retrieve_respects_top_k_with_mock_store() -> None:
    store = MagicMock()
    store.candidate_names.return_value = []
    store.collection.get.return_value = {"metadatas": []}
    store.query.return_value = [
        RetrievedChunk(
            text=f"chunk {i}",
            candidate_name="X",
            source_file="x.pdf",
            section="Skills",
            score=0.9 - i * 0.01,
            snippet=f"chunk {i}",
        )
        for i in range(10)
    ]
    hits = retrieve(store, "Python skills", top_k=4, min_score=0.65)
    assert len(hits) <= 4


def test_retrieve_skill_query_diversifies_candidates() -> None:
    store = MagicMock()
    store.candidate_names.return_value = []
    store.collection.get.return_value = {"metadatas": []}

    def _chunk(name: str, section: str, score: float, text: str) -> RetrievedChunk:
        return RetrievedChunk(
            text=text,
            candidate_name=name,
            source_file=f"{name.casefold().replace(' ', '-')}.pdf",
            section=section,
            score=score,
            snippet=text,
        )

    # Many high-score React chunks from Emma would otherwise crowd out others.
    store.query.return_value = [
        _chunk("Emma Wright", "Experience", 0.95, "React at Pixel Labs"),
        _chunk("Emma Wright", "Projects", 0.94, "React dashboard"),
        _chunk("Emma Wright", "Skills", 0.93, "React TypeScript"),
        _chunk("Lucía Fernández", "Habilidades", 0.88, "React Node.js"),
        _chunk("Tom Wilson", "Skills", 0.86, "React AWS"),
        _chunk("Rosa Diaz", "Experience", 0.84, "Built UI with React"),
    ]
    hits = retrieve(store, "quién sabe React", top_k=4, min_score=0.65)
    names = [h.candidate_name for h in hits]
    assert len(hits) == 4
    assert len(set(names)) == 4
    # Prefer Skills/Habilidades when available for that candidate.
    by_name = {h.candidate_name: h for h in hits}
    assert by_name["Emma Wright"].section == "Skills"
    assert by_name["Lucía Fernández"].section == "Habilidades"
