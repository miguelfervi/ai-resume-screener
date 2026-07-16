# Development Guide

> How to work on this repo day-to-day — commit discipline, local setup, and verification checkpoints.

## Commit workflow

Each feature maps to **one atomic commit** with a conventional message:

| Prefix | Use for |
|--------|---------|
| `chore:` | Scaffold, tooling, cursor rules |
| `feat(backend):` | Python modules, agents, API |
| `feat(frontend):` | React components, hooks, styles |
| `feat(rag):` | Chunker, store, retriever |
| `feat(agents):` | LangGraph agent nodes |
| `feat(api):` | FastAPI endpoints |
| `feat(cvs):` | CV templates and generated data |
| `data:` | Committed PDFs, manifest |
| `test:` | pytest suites |
| `docs:` | README, ARCHITECTURE |
| `ci:` | GitHub Actions |

After each commit:

1. Add a row to the **Development Log** in `README.md` with the real hash (`git log -1 --format='%h'`).
2. Smoke-test: `curl http://localhost:8000/health` (backend) or `npm run dev` (frontend).
3. At phase boundaries, add a **Changelog** entry (see README).

## Local setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GOOGLE_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### Data pipelines (offline)

```bash
# From repo root, with backend venv active
python scripts/generate_cvs.py --count 28
python scripts/ingest.py
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GOOGLE_API_KEY` | — | Gemini chat + embeddings |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Chat model |
| `GEMINI_EMBEDDING_MODEL` | `text-embedding-004` | Embeddings |
| `CHROMA_PATH` | `../data/chroma` | Vector store |
| `CVS_PATH` | `../data/cvs` | PDF directory |
| `RETRIEVAL_TOP_K` | `6` | Chunks per query |
| `RETRIEVAL_MIN_SCORE` | `0.65` | Evidence threshold |

## Testing

```bash
cd backend
pytest -v
```

Coverage targets: invariants (unit), agents (mocked LLM), API (TestClient).

## Phase checkpoints

| Phase | Commits | Verify |
|-------|---------|--------|
| Backend core | 3–8 | `GET /health` → `{"status":"ok"}` |
| CV generation | 9–13 | 28 PDFs + `manifest.json` |
| RAG ingest | 14–17 | `scripts/ingest.py` completes |
| Chat + API | 18–21 | `POST /api/chat` returns sources |
| Tests | 22–24 | `pytest` green |
| Frontend | 25–32 | Chat UI with source badges |
| Docs + CI | 33–35 | README complete, Actions pass |

## Cursor rules

`.cursor/rules/` provides persistent context for AI-assisted development:

- `project-context.mdc` — always on; stack and agent overview
- `backend-patterns.mdc` — active on `backend/**/*.py`
- `frontend-patterns.mdc` — active on `frontend/src/**/*.{ts,tsx}`
