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

## Backend layout

```
backend/app/
├── main.py              # app factory — mounts routers only
├── schemas/             # Pydantic types by domain (chat, cv, rag)
├── api/routes/          # FastAPI routers (health, chat, reindex)
├── agents/              # LangGraph pipelines
└── rag/                 # chunker, store, retriever
```

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
pnpm install
pnpm dev   # http://localhost:5173
```

### Data pipelines (offline)

```bash
# From repo root, with backend venv active
pip install -r backend/requirements.txt
python scripts/enrich_profiles.py       # expand seed with fuller experience/skills (idempotent-ish)
python scripts/generate_cvs.py          # seed → 30 PDFs; AI photos for 6 sample CVs
python scripts/generate_cvs.py --photos all   # photos for every CV (slow)
python scripts/ingest.py                # PDFs → ChromaDB (once ingest agent exists)
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

### Backend

```bash
cd backend
pytest -v
```

Coverage targets: invariants (unit), chunker/store/retriever, agents (mocked LLM), API (TestClient). No live Gemini calls in CI.

### Frontend

```bash
cd frontend
pnpm test        # Vitest — once setup (plan #50)
pnpm build
```

Coverage targets: `api.ts` mock/real paths, `useChat`, smoke RTL for chat components.

### CI (planned)

GitHub Actions on PR: `pytest` + `pnpm test` + `pnpm build`.

## Phase checkpoints

| Phase | Commits | Verify |
|-------|---------|--------|
| Backend core | 3–8 | `GET /health` → `{"status":"ok"}` |
| CV generation | 9–13 | PDFs + `manifest.json` |
| Frontend UI | 25–32 | Chat UI with mock + source badges |
| RAG ingest | 14–17 | `scripts/ingest.py` completes |
| Chat + API | 18–21 | `POST /api/chat` returns sources |
| Connect | 33–34 | `USE_MOCK=false`, docs synced |
| Backend tests | 40–46 | `pytest` green |
| Frontend tests | 50–53 | `pnpm test` green |
| CI | 60 | Actions pass |

## Cursor rules

`.cursor/rules/` is committed — shared AI context for the project. Local Cursor cache/state stays gitignored.

- `project-context.mdc` — always on
- `backend-patterns.mdc` — `backend/**/*.py`
- `frontend-patterns.mdc` — `frontend/src/**/*.{ts,tsx}`
