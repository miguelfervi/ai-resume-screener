# Architecture

Overview of the AI Resume Screener end-to-end workflow.

## Overview diagram

```mermaid
flowchart TB
  subgraph Offline["1 · Offline data preparation"]
    Seed["data/seed/profiles.json"]
    Gen["scripts/generate_cvs.py\n+ ReportLab (+ optional AI photos)"]
    PDFs["data/cvs/*.pdf\n30 résumés · 5 layouts"]
    Seed --> Gen --> PDFs
  end

  subgraph Index["2 · Offline RAG indexing"]
    Ingest["scripts/ingest.py\nLangGraph ingest_agent"]
    Extract["extract_text\npymupdf4llm"]
    Chunk["chunk_by_section"]
    Embed["embed\nGemini gemini-embedding-001"]
    Chroma["ChromaDB\ndata/chroma/"]
    PDFs --> Ingest --> Extract --> Chunk --> Embed --> Chroma
  end

  subgraph Runtime["3 · Runtime Q&A"]
    UI["React chat UI\nlocalhost:5173"]
    API["FastAPI\nPOST /api/chat"]
    Retrieve["retrieve\n(+ boosters)"]
    Validate["validate_context\nmin score gate"]
    Generate["generate_answer\nGemini chat"]
    Cite["cite_sources"]
    Answer["Answer + source badges"]
    Preview["GET /api/cvs/{file}\nPDF side panel"]

    UI -->|question| API
    API --> Retrieve
    Chroma --> Retrieve
    Retrieve --> Validate
    Validate -->|enough evidence| Generate --> Cite --> Answer
    Validate -->|weak retrieval| NoEv["No-evidence reply"]
    Answer --> UI
    UI -->|click source| Preview
    PDFs --> Preview
  end
```

### Same flow (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│  OFFLINE                                                         │
│  profiles.json → generate_cvs.py → 30 PDFs                       │
│       ↓                                                          │
│  ingest.py: extract → chunk → embed → ChromaDB                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RUNTIME                                                         │
│  Chat UI ──POST /api/chat──► retrieve (+ boosters)               │
│                               → validate_context                 │
│                               → generate_answer (Gemini)         │
│                               → cite_sources                     │
│  UI shows answer + sources                                       │
│  Click source ──GET /api/cvs/{file}──► PDF preview panel         │
└─────────────────────────────────────────────────────────────────┘
```

## LangGraph agents

| Agent | When | Nodes |
|-------|------|-------|
| **ingest** | `scripts/ingest.py` or `POST /api/reindex` | extract → chunk → embed/store → verify |
| **chat** | each user question | retrieve → validate → generate → cite |

CV PDFs are **not** generated inside LangGraph — only offline from seed JSON.

## Backend layout

```
backend/app/
├── main.py
├── config.py / llm.py / invariants.py / metrics.py
├── cv_renderer.py / photo_generator.py / extractors.py
├── schemas/          # chat, cv, rag
├── api/routes/       # health, chat, reindex, cvs
├── agents/           # ingest_agent, chat_agent
└── rag/              # chunker, store, retriever
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness + `indexReady` |
| `POST` | `/api/chat` | Question → grounded answer + sources + metrics |
| `POST` | `/api/reindex` | Rebuild Chroma index from `data/cvs/` |
| `GET` | `/api/cvs/{filename}` | Serve CV PDF for the side panel |

## Key decisions

| Decision | Why |
|----------|-----|
| Seed JSON + ReportLab | Fast, reproducible demo CVs; RAG is the core deliverable |
| Two LangGraph agents | Clear split: index offline vs answer online |
| `validate_context` | Blocks low-score retrieval → fewer hallucinations |
| Retrieval boosters | Names, skills, roles, sections, institutions (EN/ES cues) without dumping the global threshold |
| ChromaDB local | Zero infra; cosine space so `score = 1 − distance` aligns with `RETRIEVAL_MIN_SCORE` |
| Vite + React | SPA chat; no SSR needed |
| Quota errors → HTTP 429 | Free-tier Gemini limits surface as a clear UI message |

## Data layout

- `data/seed/profiles.json` — candidate profiles
- `data/cvs/*.pdf` — 30 generated résumés (committed)
- `data/cvs/photos/` — AI headshots for sample CVs
- `data/cvs/manifest.json` — generation metadata
- `data/chroma/` — vector index (gitignored)

## Demo questions

- Who has experience with Python?
- Which candidate graduated from UPC?
- Summarize the profile of Jane Doe.
