# Architecture

> Design document for the AI Resume Screener.

## High-level flow

```
1. Generate 28 demo CV PDFs from seed JSON (offline, no LLM)
2. Extract text → chunk → embed → store in ChromaDB (offline)
3. User asks questions via chat UI → retrieve chunks → LLM answer + sources
```

## Backend structure

```
backend/app/
├── main.py                 # FastAPI app factory, mounts routers
├── config.py               # pydantic-settings
├── llm.py                  # Gemini chat + embeddings factory
├── cv_renderer.py          # ReportLab PDF builder (seed → PDF)
├── invariants.py           # runtime guards
├── metrics.py              # RunMetrics + Timer
├── extractors.py           # PDF → text
├── schemas/
│   ├── chat.py             # API types
│   ├── cv.py               # CV / manifest types
│   └── rag.py              # RAG domain
├── api/
│   ├── deps.py
│   └── routes/
│       ├── health.py
│       ├── chat.py         # planned
│       └── reindex.py      # planned
├── agents/
│   ├── ingest_agent.py     # offline RAG indexing
│   └── chat_agent.py       # runtime Q&A
└── rag/
    ├── chunker.py
    ├── store.py
    └── retriever.py
```

## CV generation (simplified)

No LangGraph, no Gemini, no browser. One script:

```
data/seed/profiles.json  →  scripts/generate_cvs.py  →  data/cvs/*.pdf + manifest.json
```

`cv_renderer.py` uses ReportLab to render a clean A4 PDF per profile.

## LangGraph agents (2, not 3)

| Agent | Purpose | Nodes |
|-------|---------|-------|
| **ingest** | Build vector index | extract → chunk → embed → store → verify |
| **chat** | Answer questions | retrieve → validate context → generate → cite sources |

## Key design decisions

| Decision | Rationale |
|----------|-----------|
| Seed PDFs + ReportLab | Fastest path to demo data; RAG is the core deliverable |
| Vite + React (not Next.js) | Single-page chat; no SSR needed |
| `schemas/` + `api/routes/` | Keeps main.py thin |
| ChromaDB | Zero infra; fine for local prototype |
| Runtime invariants | Guard against hallucinations and empty indexes |

## Data layout

- `data/seed/profiles.json` — 28 hand-crafted candidate profiles
- `data/cvs/*.pdf` — generated resumes (committed for demo)
- `data/cvs/manifest.json` — metadata index for validation and citations
- `data/chroma/` — persistent vector store (gitignored)

## API (planned)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness + index status |
| POST | `/api/chat` | Question → answer + sources |
| POST | `/api/reindex` | Rebuild ChromaDB index |

## Demo questions

- Who has experience with Python?
- Which candidate graduated from UPC?
- Summarize the profile of Jane Doe.
