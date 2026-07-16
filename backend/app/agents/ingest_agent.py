from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ..config import Settings, get_settings
from ..extractors import extract_text_from_path
from ..invariants import check_pdf_exists
from ..llm import build_embeddings
from ..metrics import RunMetrics, Timer
from ..rag.chunker import chunk_document
from ..rag.store import ChromaStore
from ..schemas import DocumentChunk

logger = logging.getLogger("resume_screener.ingest")


class IngestState(TypedDict, total=False):
    cvs_dir: str
    manifest_path: str
    reset: bool
    pdf_paths: list[str]
    extracted: list[dict[str, str]]
    chunks: list[dict[str, Any]]
    stored_count: int
    doc_count: int
    metrics: dict[str, Any]
    error: str


def _metrics(state: IngestState) -> RunMetrics:
    raw = state.get("metrics") or {}
    m = RunMetrics()
    m.provider = raw.get("provider", "gemini")
    m.node_timings_ms = dict(raw.get("node_timings_ms") or {})
    m.input_tokens = int(raw.get("input_tokens") or 0)
    m.output_tokens = int(raw.get("output_tokens") or 0)
    m.chunks_retrieved = int(raw.get("chunks_retrieved") or 0)
    m.sources_cited = int(raw.get("sources_cited") or 0)
    m.success = bool(raw.get("success", False))
    m.total_ms = float(raw.get("total_ms") or 0)
    return m


def load_manifest(state: IngestState) -> dict:
    cvs_dir = Path(state["cvs_dir"])
    manifest_path = Path(state.get("manifest_path") or cvs_dir / "manifest.json")
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths: list[str] = []
    for entry in entries:
        pdf = cvs_dir / entry["file"]
        check_pdf_exists(pdf)
        paths.append(str(pdf))
    return {"pdf_paths": paths}


def extract_pdfs(state: IngestState) -> dict:
    metrics = _metrics(state)
    extracted: list[dict[str, str]] = []
    with Timer(metrics.node_timings_ms, "extract"):
        for path_str in state.get("pdf_paths") or []:
            path = Path(path_str)
            text = extract_text_from_path(path)
            # candidate name from filename stem as fallback
            name = path.stem.replace("-", " ").title()
            extracted.append(
                {
                    "text": text,
                    "candidate_name": name,
                    "source_file": path.name,
                }
            )
    # Prefer manifest names when available
    cvs_dir = Path(state["cvs_dir"])
    manifest_path = Path(state.get("manifest_path") or cvs_dir / "manifest.json")
    if manifest_path.is_file():
        by_file = {
            e["file"]: e["full_name"]
            for e in json.loads(manifest_path.read_text(encoding="utf-8"))
        }
        for item in extracted:
            if item["source_file"] in by_file:
                item["candidate_name"] = by_file[item["source_file"]]

    return {"extracted": extracted, "metrics": metrics.to_dict()}


def chunk_all(state: IngestState, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    metrics = _metrics(state)
    all_chunks: list[dict[str, Any]] = []
    with Timer(metrics.node_timings_ms, "chunk"):
        for item in state.get("extracted") or []:
            chunks = chunk_document(
                item["text"],
                candidate_name=item["candidate_name"],
                source_file=item["source_file"],
                chunk_size_tokens=settings.chunk_size_tokens,
                chunk_overlap_tokens=settings.chunk_overlap_tokens,
            )
            all_chunks.extend([c.model_dump() for c in chunks])
    return {"chunks": all_chunks, "metrics": metrics.to_dict()}


def embed_and_store(state: IngestState, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    metrics = _metrics(state)
    embeddings = build_embeddings(settings)
    store = ChromaStore(settings.chroma_dir, embeddings=embeddings)

    with Timer(metrics.node_timings_ms, "embed_store"):
        if state.get("reset"):
            store.reset()
        chunks = [DocumentChunk.model_validate(c) for c in state.get("chunks") or []]
        stored = store.add_chunks(chunks)

    return {"stored_count": stored, "metrics": metrics.to_dict()}


def verify_index(state: IngestState, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    metrics = _metrics(state)
    embeddings = build_embeddings(settings)
    store = ChromaStore(settings.chroma_dir, embeddings=embeddings)
    with Timer(metrics.node_timings_ms, "verify"):
        count = store.verify(min_docs=1)
    metrics.success = True
    metrics.total_ms = sum(metrics.node_timings_ms.values())
    return {"doc_count": count, "metrics": metrics.to_dict()}


def build_ingest_graph(settings: Settings | None = None):
    settings = settings or get_settings()

    def _chunk(state: IngestState) -> dict:
        return chunk_all(state, settings)

    def _store(state: IngestState) -> dict:
        return embed_and_store(state, settings)

    def _verify(state: IngestState) -> dict:
        return verify_index(state, settings)

    graph = StateGraph(IngestState)
    graph.add_node("load_manifest", load_manifest)
    graph.add_node("extract", extract_pdfs)
    graph.add_node("chunk", _chunk)
    graph.add_node("embed_store", _store)
    graph.add_node("verify", _verify)
    graph.add_edge(START, "load_manifest")
    graph.add_edge("load_manifest", "extract")
    graph.add_edge("extract", "chunk")
    graph.add_edge("chunk", "embed_store")
    graph.add_edge("embed_store", "verify")
    graph.add_edge("verify", END)
    return graph.compile()


def run_ingest(
    *,
    cvs_dir: Path | None = None,
    reset: bool = True,
    settings: Settings | None = None,
) -> IngestState:
    settings = settings or get_settings()
    cvs = cvs_dir or settings.cvs_dir
    app = build_ingest_graph(settings)
    result = app.invoke(
        {
            "cvs_dir": str(cvs),
            "manifest_path": str(cvs / "manifest.json"),
            "reset": reset,
            "metrics": RunMetrics(provider="gemini").to_dict(),
        }
    )
    logger.info(
        "ingest done docs=%s stored=%s metrics=%s",
        result.get("doc_count"),
        result.get("stored_count"),
        result.get("metrics"),
    )
    return result
