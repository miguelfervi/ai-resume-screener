# Architecture

> Design document for the AI Resume Screener. Implementation is manual — this file describes the intended system.

## High-level flow

```
1. Generate 25–30 fake CV PDFs (offline)
2. Extract text → chunk → embed → store in ChromaDB (offline)
3. User asks questions via chat UI → retrieve chunks → LLM answer + sources
```

## Planned agents (LangGraph)

| Agent | Purpose | Nodes |
|-------|---------|-------|
| **generate** | Create fake CV PDFs | plan → content → photo → render PDF → validate manifest |
| **ingest** | Build vector index | extract → chunk → embed → store → verify |
| **chat** | Answer questions | retrieve → validate context → generate → cite sources |

## Key design decisions

| Decision | Rationale |
|----------|-----------|
| Vite + React (not Next.js) | Single-page chat; no SSR needed |
| ChromaDB | Zero infra; fine for local prototype |
| Runtime invariants | Guard against hallucinations and empty indexes |
| Seed profiles | Optional offline CV generation without API calls |

## Data layout

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
