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
  trained TF-IDF + Logistic Regression classifier (95.4% test accuracy) —
  built specifically to support a three-way comparison in the capstone
  report.
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

## Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the full Render setup, including
the two manual wiring steps required by the frontend's no-build-step
design.

## Tests

53 backend tests + 9 frontend tests across all milestones — see each
component's README for how to run them.
