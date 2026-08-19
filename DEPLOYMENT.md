# Deployment guide — HH Goa 2026 Task 2

Targets per the master prompt: backend on Render, frontend on Vercel.
Everything below is what a teammate with dashboard access has to run; the repo is
already wired for it (Dockerfile, render.yaml, vercel.json, `VITE_API_BASE`).

## 1. Backend — Render

1. Push this repo to GitHub.
2. Render dashboard → **New > Blueprint** → select the repo. `render.yaml` is read
   automatically. It creates one Docker web service.
3. In the service's **Environment** tab set:
   - `SARVAM_API_KEY` — paste your Sarvam key (enables STT).
   - Optionally override `AA_LLM_MODEL` / `AA_EMBEDDING_MODEL` for your tier.
4. Plan: `starter` (or better). The free 512 MB plan is too tight for the models +
   FAISS index; if you must stay free, rebuild with a smaller index:
   `docker build --build-arg INDEX_LIMIT=4000 .`
5. Wait for the build (it compiles the offline index at build time, so the first
   deploy takes several minutes). Verify: `https://<service>.onrender.com/api/health`
   returns `{"status":"ok"}`.
6. Note the service URL, e.g. `https://hh-goa-ask-anything-backend.onrender.com`.

### Rebuilds
Render rebuilds the image on every push that touches `backend/**` or
`data/passages.jsonl`. First request after a cold start pays model warm-up
(≈30–40 s) — expected and fine.

## 2. Frontend — Vercel

1. Vercel dashboard → **Add New Project** → import the repo → **Frontend Directory:
   `frontend`** (Framework Preset: **Other** — the app is TanStack Start SSR
   running on a Nitro server function, not a static Vite SPA).
2. Environment variable: `VITE_API_BASE=https://<your-backend>.onrender.com`
   (the URL from step 1.6, no trailing slash). It is inlined at build time, so set
   it before deploying; locally it defaults to `http://127.0.0.1:8001`.
3. Deploy. `vercel.json` (`framework: null`, `buildCommand: npm run build`) makes
   Vercel run the Nitro build, which emits `.vercel/output` (Build Output API v3) —
   static assets plus the `__server` SSR function. `/api/...` calls are NOT proxied
   here; the browser talks straight to the Render backend at `VITE_API_BASE`
   (allowed by the backend's `allow_origins=["*"]`).

## 3. Verify live

- Open the Vercel URL from a clean/incognito browser (no localhost).
- Ask a text query → answer + sources + confidence/latency render.
- Click the mic → grant permission → record → transcript appears → answer returns
  (only works once `SARVAM_API_KEY` is set on the backend).
- `/api/benchmarks` on the deployed backend returns the last benchmark numbers;
  the Stats panel on the live site reads them.

## 4. Local sanity before deploying (optional)

```bash
# build the image locally (Docker required)
docker build -t hh-goa-backend --build-arg INDEX_LIMIT=12000 .
docker run --rm -p 8000:8000 -e AA_FORCE_CPU=1 hh-goa-backend
curl http://localhost:8000/api/health
```

## 5. After going live

- Run `python -m benchmarks.run_voice_latency_bench` with a Sarvam key and
  `data/voice_samples/*.wav` clips to fill the end-to-end voice latency row.
- Update the README live-link + voice-latency rows, commit, and re-deploy so the
  README ships the real numbers.
