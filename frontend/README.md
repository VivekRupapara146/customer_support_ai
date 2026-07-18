# TechMart Support — Frontend

Plain HTML/CSS/JS, no build step, no framework — deliberately simple
(Instruction 5) since the backend is the actual capstone subject.

## Run it

The backend needs a stable origin for CORS, so don't open `index.html`
directly via `file://` — serve it from a tiny static server instead:

```bash
cd frontend
python3 -m http.server 3000
```

Then open **http://localhost:3000** in your browser. Make sure the
backend is also running (`uvicorn main:app --reload` from `backend/`)
and that `CORS_ALLOWED_ORIGINS` in `backend/.env` includes
`http://localhost:3000` (it does by default).

## What it does

- Sign in (Milestone 1's auth stub — any username/password works)
- Send a message → routed through whichever router is active
  (`ACTIVE_ROUTER` in the backend's `.env`) → grounded RAG answer
- Each assistant reply shows tags for which specialist(s) answered
- The sidebar's 5 status lights up to match — a live view of the
  multi-agent routing, not just a plain chat log
- Replies that hit the retrieval-confidence fallback (honest "I don't
  know") are visually distinguished with an amber border, instead of
  looking identical to a grounded answer
- "New conversation" starts a fresh `session_id`; history persists
  server-side per session (Milestone 5) even though this UI doesn't yet
  have a history browser — the API (`GET /chat/history/{id}`) is there
  if you want to add one later

## Security note

The JWT is kept in a JS variable only — never `localStorage` — since
`localStorage` is readable by any script on the page (a common XSS
target). Trade-off: refreshing the page requires signing in again.
Deliberate choice, not an oversight.

## Testing

`app.js`'s pure logic (fallback detection, session-id validation,
agent-list sanitization) is unit-tested under Node, no browser needed:

```bash
node app.test.js
```
