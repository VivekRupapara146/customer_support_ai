# Deploying to Render

## What this deploys
- **Backend**: Dockerized FastAPI service (`backend/Dockerfile`)
- **Frontend**: plain static site (`frontend/`), no build step

## One-time setup before deploying

1. **Gemini API key** — from your existing Inquira AI project.
2. **MongoDB Atlas URI** — the same one you've been using locally. Make
   sure Atlas's Network Access allows connections from anywhere
   (`0.0.0.0/0`), since Render's IPs aren't static. (Same tradeoff we
   discussed for local dev — fine for a capstone demo, document it as a
   known simplification.)
3. **Demo password hash** — run this locally first:
   ```bash
   cd backend
   python -m scripts.generate_password_hash
   ```
   Save the printed hash — you'll paste it into Render's dashboard, not
   into any file that gets committed.

## Deploy steps

1. Push this repo to GitHub (Render deploys from a Git repo, not a raw
   zip upload).
2. In the Render dashboard: **New → Blueprint**, point it at your repo.
   Render will read `render.yaml` at the repo root and propose both
   services.
3. Before clicking deploy, Render will prompt you for every `sync: false`
   env var (these are intentionally left out of `render.yaml` — they're
   secrets, never committed to Git):
   - `MONGO_URI`
   - `GEMINI_API_KEY`
   - `DEMO_PASSWORD_HASH` (from step 3 above)
   - `CORS_ALLOWED_ORIGINS` — leave a placeholder for now (e.g.
     `http://localhost:3000`); you'll update it in step 5.
4. Deploy. Render builds the Docker image and serves the static site.
   Note the backend's public URL (something like
   `https://techmart-support-backend.onrender.com`).

## Two manual wiring steps (unavoidable with a build-step-free static site)

Because the frontend has no build process, Render can't automatically
inject the backend's URL into it (that only works for services with an
actual build step) — so two small manual edits are needed after first
deploy:

5. **Point the frontend at the real backend**: edit
   `frontend/config.js`:
   ```js
   window.TECHMART_CONFIG = {
     apiBaseUrl: "https://techmart-support-backend.onrender.com",
   };
   ```
   Commit and push — Render auto-redeploys the static site.

6. **Point the backend's CORS allowlist at the real frontend**: in
   Render's dashboard, edit the backend service's `CORS_ALLOWED_ORIGINS`
   env var to the frontend's actual URL (e.g.
   `https://techmart-support-frontend.onrender.com`), then manually
   redeploy the backend (env var changes need a redeploy to take effect).

## After deploying — sanity checks

- `GET https://<backend-url>/health` → should return `200` with
  `"database": "connected"`
- Open the frontend URL → sign in with your demo username/password → send
  a message → confirm a grounded answer comes back with the right
  specialist tag

## Known limitations to disclose (good material for your capstone report)

- **Render's free tier spins down on inactivity** — the first request
  after idling can take 30-60 seconds while the container cold-starts.
  Not a bug; a free-tier characteristic.
- **Single demo credential, not real user accounts** — acceptable for a
  capstone demo link, not for a real multi-user product.
- **`0.0.0.0/0` on Atlas** — same tradeoff as local dev, now more
  consequential since the deployed backend is publicly reachable. Your
  Mongo username/password become the only real access control.
