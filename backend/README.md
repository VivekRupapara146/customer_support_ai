# TechMart Support — Backend

FastAPI backend for the multi-agent RAG customer support system. See the
repo root's `DEPLOYMENT.md` for hosting this on Render.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in real values
```

Required in `.env`: `JWT_SECRET_KEY`, `MONGO_URI`, `GEMINI_API_KEY`.
Everything else has a sensible default — see `.env.example` for the full
list and comments.

## Run

```bash
uvicorn main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive API docs.

## Test

```bash
pip install -r requirements-dev.txt   # adds mongomock-motor for offline DB tests
python tests/test_rag_pipeline.py
python tests/test_milestone3.py
python tests/test_milestone4.py
python tests/test_milestone5.py
python tests/test_milestone6.py
python tests/test_milestone7.py
python tests/test_milestone9.py
python tests/test_milestone10_auth.py
```

All test files are self-contained scripts (no pytest required) — each
prints PASS/FAIL per case and exits non-zero on failure.

## Train Router v2b (optional — a trained artifact ships already)

```bash
python -m ml.train_router_v2b
```

Re-downloads aren't automatic — `banking77_train.csv` / `banking77_test.csv`
must be present in `backend/` (gitignored; see repo root for the source).

## Project layout

```
backend/
├── main.py              # app entrypoint
├── core/                # config, logging, rate limiting, security
├── auth/                # JWT + demo credential login
├── database/            # MongoDB connection + conversation storage
├── models/              # Pydantic schemas
├── rag/                 # chunking, embeddings, FAISS store, retrieval
├── router/               # 3 router implementations (v1/v2/v2b)
├── agents/               # generic RAG agent + base interface
├── prompts/              # system prompts, kept separate from logic
├── ml/                   # Router v2b training + Banking77 mapping
├── api/                  # /health, /chat routes
├── scripts/              # one-off ops helpers (password hash generator)
└── tests/                # per-milestone test suites
```
