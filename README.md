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
| CV generation | Jinja2 HTML template · Playwright PDF export |

## Project structure

```
ai-resume-screener/
├── backend/           # FastAPI app, agents, RAG pipeline
├── frontend/          # React chat UI
├── data/
│   ├── cvs/           # Generated PDF resumes + manifest
│   ├── templates/     # HTML template for CV rendering
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

| # | Commit | Date | Summary |
|---|--------|------|---------|
| 1 | `5643bde` | 2026-07-16 | Project scaffold — folders, .gitignore, README skeleton |
| 2 | `37af187` | 2026-07-16 | Cursor rules + docs/DEVELOPMENT.md |
| 3 | `7a50c26` | 2026-07-16 | Backend config, requirements.txt, .env.example |

## License

Private — technical assessment project.
