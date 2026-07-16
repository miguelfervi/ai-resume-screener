# AI Resume Screener

> RAG chat prototype for screening a collection of PDF resumes — technical task.

## Overview

Full-stack application that lets recruiters ask natural-language questions about a set of CV PDFs. The system extracts text from PDFs, indexes content for retrieval, and answers questions grounded in CV data with optional source citations.

## Planned stack

| Layer | Technology |
|-------|------------|
| Frontend | Vite · React 19 · TypeScript · Tailwind CSS v4 · shadcn/ui |
| Backend | FastAPI · Python 3.11+ · LangGraph |
| LLM / Embeddings | Google Gemini (configurable) |
| Vector store | ChromaDB (local, persistent) |
| CV generation | Seed JSON · ReportLab PDF · `scripts/generate_cvs.py` |

## Project structure

```
ai-resume-screener/
├── backend/           # FastAPI app, agents, RAG pipeline
├── frontend/          # React chat UI
├── data/
│   ├── cvs/           # Generated PDF resumes + manifest
│   ├── seed/          # Hand-crafted candidate profiles (JSON)
│   └── chroma/        # Vector index (gitignored)
├── scripts/           # CLI: generate CVs, ingest index
└── docs/              # Architecture and design notes
```

## Getting started

Implementation is in progress. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the planned workflow and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for commit workflow and local setup.

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google AI Studio API key (when LLM features are wired up)

### Backend (placeholder)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # once dependencies are defined
uvicorn app.main:app --reload --port 8000
```

### Frontend (placeholder)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Development log

Registro cronológico de `git log` (más reciente al final de la tabla).

| Commit | Date | Message |
|--------|------|---------|
| `5643bde` | 2026-07-16 | feat: scaffold project |
| `37af187` | 2026-07-16 | chore: add cursor rules for project context |
| `7a50c26` | 2026-07-16 | feat(backend): add config and dependencies |
| `3b6f019` | 2026-07-16 | feat(backend): add pydantic models and RunMetrics |
| `37c54a8` | 2026-07-16 | feat(backend): add runtime invariants module |
| `09b4e13` | 2026-07-16 | feat(backend): add Gemini LLM factory |
| `4e271d4` | 2026-07-16 | feat(backend): add FastAPI app with health endpoint and api layer |
| `dfc92bb` | 2026-07-16 | feat(backend): add PDF text extractor |
| `337093b` | 2026-07-16 | data: add seed candidate profiles for CV generation |
| `c0e14a6` | 2026-07-16 | feat(cvs): add ReportLab PDF renderer and generate_cvs CLI |
| `cafb5fa` | 2026-07-16 | docs: update architecture for seed PDF approach |

## License

Private — technical assessment project.
