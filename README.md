# TechMart Support — Multi-Agent AI Customer Support System

A capstone project: a multi-agent, RAG-grounded customer support system
for a fictional electronics retailer, built to demonstrate real
architectural decision-making rather than just wiring an LLM to a chat box.

## Structure

```
.
├── backend/          FastAPI + RAG pipeline + 3 interchangeable routers
├── frontend/          Plain HTML/CSS/JS chat UI, no build step
├── render.yaml        Render Blueprint (deploy both services together)
└── DEPLOYMENT.md       Full deployment walkthrough
```

Each half has its own README with setup/run/test instructions:
- [`backend/README.md`](backend/README.md)
- [`frontend/README.md`](frontend/README.md)

## Quick start (local)

1. `backend/` — copy `.env.example` to `.env`, fill in `MONGO_URI` and
   `GEMINI_API_KEY`, then `pip install -r requirements.txt` and
   `uvicorn main:app --reload`.
2. `frontend/` — `python3 -m http.server 3000`, then open
   `http://localhost:3000`.

## What makes this more than a chat wrapper

- **3 interchangeable routers** behind one interface: rule-based keyword
  matching, an LLM-based structured-output classifier, and a Banking77-
  trained TF-IDF + Logistic Regression classifier — built specifically to
  support a measured three-way comparison (table below). The Banking77
  model scores 95.4% on Banking77's own test set but only a 30% hit rate on
  TechMart queries: a measured domain-transfer gap, which is why it is not
  the default router.
- **RAG grounding with an honesty guarantee**: retrieval confidence below
  threshold triggers an explicit "I don't know" rather than letting the
  LLM improvise.
- **Multi-agent aggregation**: a single query can span multiple
  specialists (e.g. a billing issue that's also a technical one), and
  responses are merged, not just single-routed.
- **Security built in from Milestone 1**, not retrofitted: JWT auth,
  rate limiting, CORS, security headers, prompt-injection mitigation, and
  a startup guard that refuses to boot in production with placeholder
  secrets.
- **Domain-filtered retrieval**: each agent only searches its own mapped
  knowledge base documents (e.g., billing can never retrieve product
  content), with one deliberate overlap (Premium subscription content is
  shared between billing and technical, since it genuinely spans both).
- **Conversation history**: past conversations are listed and reloadable
  from the sidebar, backed by MongoDB with per-user ownership isolation.
- **CI**: every push runs the full test suite (backend + frontend)
  automatically via GitHub Actions — fully offline, no live credentials
  needed in CI.

## Router comparison

Evaluated on 30 hand-labeled TechMart queries (single-domain, multi-domain,
messy phrasing, ambiguous). *Hit rate* = at least one predicted agent is
correct; *exact match* = predicted set equals the expected set.

| Router | Hit rate | Exact match | Avg latency | Marginal cost |
|---|---|---|---|---|
| v1 — Rule-based (default) | 73.3% | 40.0% | 0.01 ms | none (local) |
| v2 — LLM-based (Gemini) | 86.7% | 50.0% | 478 ms | 1 LLM call / query |
| v2b — TF-IDF + LR (Banking77) | 30.0% | 10.0% | 84 ms | none (local) |

The LLM router is the most accurate; rule-based is the default because it is
free and instant. 30 queries is a small set, so treat differences as
directional. Full per-category breakdown and caveats:
[`backend/eval/router_comparison_report.md`](backend/eval/router_comparison_report.md).

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the full Render setup, including
the two manual wiring steps required by the frontend's no-build-step
design.

## Tests

86 backend checks (13 files) + 18 frontend checks — see each component's
README for how to run them. CI runs all of them automatically on every push
via `.github/workflows/tests.yml`.
