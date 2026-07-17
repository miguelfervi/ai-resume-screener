from __future__ import annotations

import logging
import re
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ..config import Settings, get_settings
from ..invariants import (
    check_answer_grounded,
    check_retrieval_has_evidence,
    check_sources_from_retrieved,
)
from ..llm import build_embeddings, invoke_chat_with_fallback
from ..metrics import RunMetrics, Timer
from ..rag.retriever import retrieve
from ..rag.store import ChromaStore
from ..schemas import RetrievedChunk, Source

logger = logging.getLogger("resume_screener.chat")

_NO_EVIDENCE = (
    "I could not find enough evidence in the indexed CVs to answer that confidently."
)


class ChatState(TypedDict, total=False):
    question: str
    history: list[dict[str, str]]
    retrieved: list[dict[str, Any]]
    context_ok: bool
    answer: str
    sources: list[dict[str, Any]]
    metrics: dict[str, Any]


def _metrics(state: ChatState) -> RunMetrics:
    raw = state.get("metrics") or {}
    m = RunMetrics(provider=raw.get("provider", "gemini"))
    m.model = str(raw.get("model") or "")
    m.node_timings_ms = dict(raw.get("node_timings_ms") or {})
    m.input_tokens = int(raw.get("input_tokens") or 0)
    m.output_tokens = int(raw.get("output_tokens") or 0)
    m.chunks_retrieved = int(raw.get("chunks_retrieved") or 0)
    m.sources_cited = int(raw.get("sources_cited") or 0)
    m.success = bool(raw.get("success", False))
    m.total_ms = float(raw.get("total_ms") or 0)
    return m


def retrieve_node(state: ChatState, settings: Settings) -> dict:
    metrics = _metrics(state)
    embeddings = build_embeddings(settings)
    store = ChromaStore(settings.chroma_dir, embeddings=embeddings)
    with Timer(metrics.node_timings_ms, "retrieve"):
        chunks = retrieve(
            store,
            state["question"],
            top_k=settings.retrieval_top_k,
            min_score=settings.retrieval_min_score,
        )
    metrics.chunks_retrieved = len(chunks)
    return {
        "retrieved": [c.model_dump() for c in chunks],
        "metrics": metrics.to_dict(),
    }


def validate_context(state: ChatState, settings: Settings) -> dict:
    metrics = _metrics(state)
    chunks = [RetrievedChunk.model_validate(c) for c in state.get("retrieved") or []]
    strong = [c for c in chunks if c.score >= settings.retrieval_min_score][: settings.retrieval_top_k]
    ok = len(strong) > 0
    if ok:
        try:
            check_retrieval_has_evidence(strong, settings.retrieval_min_score)
        except Exception:
            ok = False
            strong = []
    return {
        "retrieved": [c.model_dump() for c in strong],
        "context_ok": ok,
        "metrics": metrics.to_dict(),
    }


def generate_answer(state: ChatState, settings: Settings) -> dict:
    metrics = _metrics(state)
    if not state.get("context_ok"):
        return {
            "answer": _NO_EVIDENCE,
            "metrics": metrics.to_dict(),
        }

    chunks = [RetrievedChunk.model_validate(c) for c in state.get("retrieved") or []]
    context = "\n\n".join(
        f"[{c.candidate_name} | {c.source_file} | {c.section} | score={c.score}]\n{c.text}"
        for c in chunks
    )
    history_txt = ""
    for msg in state.get("history") or []:
        history_txt += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"

    prompt = (
        "You are a recruiting assistant. Answer ONLY using the CV excerpts below. "
        "If the excerpts do not support an answer, say you lack evidence. "
        "Give a useful, well-structured answer with the relevant details from the excerpts "
        "(role, experience, skills, education, etc. when present). "
        "For profile or summarize questions, cover role, location, experience, skills, "
        "and education only when those topics appear in the excerpts. "
        "Do not invent empty sections, and never write 'I lack evidence' per section — "
        "omit topics that are not supported. "
        "Do not stop at contact details or the header alone if other excerpts exist. "
        "Do not list the same skill, technology, or fact more than once; "
        "deduplicate and mention each item only once. "
        "Only name candidates when the excerpts clearly support the answer for them. "
        "Do not mention candidates who lack evidence, and do not add a 'no evidence for X' "
        "footnote for people who merely appear in unrelated excerpts. "
        "When answering about a skill or technology, mention it once per candidate "
        "(e.g. companies or years), not once per bullet that repeats the same word.\n\n"
        f"Conversation so far:\n{history_txt or '(none)'}\n"
        f"Question: {state['question']}\n\n"
        f"CV excerpts:\n{context}\n"
    )

    with Timer(metrics.node_timings_ms, "generate"):
        result = invoke_chat_with_fallback(prompt, settings)
        response = result.response
        metrics.model = result.model
        answer = getattr(response, "content", None) or str(response)
        if isinstance(answer, list):
            answer = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in answer
            )
        usage = getattr(response, "usage_metadata", None) or {}
        metrics.input_tokens = int(usage.get("input_tokens") or usage.get("input_token_count") or 0)
        metrics.output_tokens = int(
            usage.get("output_tokens") or usage.get("output_token_count") or 0
        )

    check_answer_grounded(answer, chunks, is_no_evidence_case=False)
    return {"answer": answer.strip(), "metrics": metrics.to_dict()}


def cite_sources(state: ChatState) -> dict:
    metrics = _metrics(state)
    chunks = [RetrievedChunk.model_validate(c) for c in state.get("retrieved") or []]
    if not state.get("context_ok") or not chunks:
        metrics.sources_cited = 0
        metrics.success = True
        metrics.total_ms = sum(metrics.node_timings_ms.values())
        return {"sources": [], "metrics": metrics.to_dict()}

    answer = state.get("answer") or ""
    selected: list[RetrievedChunk] = []
    for chunk in chunks:
        name = chunk.candidate_name
        # Prefer chunks whose candidate is mentioned; otherwise keep top scores.
        if name and re.search(re.escape(name.split()[0]), answer, re.IGNORECASE):
            selected.append(chunk)
    if not selected:
        selected = chunks[:3]

    # One chip per candidate: keep the highest-scoring chunk.
    best_by_candidate: dict[str, RetrievedChunk] = {}
    for chunk in selected:
        prev = best_by_candidate.get(chunk.candidate_name)
        if prev is None or chunk.score > prev.score:
            best_by_candidate[chunk.candidate_name] = chunk

    sources: list[Source] = [
        Source(
            candidate_name=chunk.candidate_name,
            file=chunk.source_file,
            section=chunk.section,
            snippet=chunk.snippet or chunk.text[:220],
            score=chunk.score,
        )
        for chunk in sorted(
            best_by_candidate.values(),
            key=lambda c: c.score,
            reverse=True,
        )
    ]

    check_sources_from_retrieved(sources, chunks)
    metrics.sources_cited = len(sources)
    metrics.success = True
    metrics.total_ms = sum(metrics.node_timings_ms.values())
    return {
        "sources": [s.model_dump() for s in sources],
        "metrics": metrics.to_dict(),
    }


def build_chat_graph(settings: Settings | None = None):
    settings = settings or get_settings()

    def _retrieve(state: ChatState) -> dict:
        return retrieve_node(state, settings)

    def _validate(state: ChatState) -> dict:
        return validate_context(state, settings)

    def _generate(state: ChatState) -> dict:
        return generate_answer(state, settings)

    graph = StateGraph(ChatState)
    graph.add_node("retrieve", _retrieve)
    graph.add_node("validate", _validate)
    graph.add_node("generate", _generate)
    graph.add_node("cite", cite_sources)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "validate")
    graph.add_edge("validate", "generate")
    graph.add_edge("generate", "cite")
    graph.add_edge("cite", END)
    return graph.compile()


def run_chat(
    question: str,
    history: list[dict[str, str]] | None = None,
    *,
    settings: Settings | None = None,
) -> ChatState:
    settings = settings or get_settings()
    app = build_chat_graph(settings)
    result = app.invoke(
        {
            "question": question,
            "history": history or [],
            "metrics": RunMetrics(provider="gemini").to_dict(),
        }
    )
    return result
