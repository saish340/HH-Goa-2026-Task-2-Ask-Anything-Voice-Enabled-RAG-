# HH Goa 2026 — Ask Anything (Voice-Enabled RAG)

This project is a local working prototype for the HH Goa 2026 Task 2 challenge. It includes a FastAPI backend, a hybrid retrieval flow, guardrails, and a dark HH Goa–inspired frontend.

## What is implemented

- FastAPI backend with a query endpoint at `/api/ask`
- Dense + BM25 hybrid retrieval with Reciprocal Rank Fusion
- Multi-strategy chunking layer with sentence, semantic, and sliding-window chunkers
- Guardrails for off-topic and low-support rejection
- Structured JSON response with query, retrieved chunks, confidence, grounded flag, and latency
- HH Goa themed React UI with voice-first hero, status line, and answer card

## Project structure

- `backend/app` — core app and API logic
- `backend/app/tests` — validation tests
- `backend/benchmarks` — latency and quality scripts
- `frontend` — React + Vite app

## Verification

Fresh local validation performed:

- Backend tests: `21 passed`
- Frontend build: `vite build` completed successfully

## Performance

Retrieval and guardrail numbers below come from the reproducible quality benchmark
(`python -m benchmarks.run_quality_bench`) run over the real offline corpus (MSMARCO-XI
sample, hybrid dense+BM25 RRF retrieval, strategy routing, reranking). Latency figures
are from `python -m benchmarks.run_latency_bench` on the same corpus (16 vCPU, CPU-only inference).

### Retrieval (MSMARCO-XI, n=150 labeled queries)
Recall@5: 84.00%
Recall@10: 88.00%
MRR: 0.576

### Behavior / guardrails (131 queries across 7 categories)
Overall accuracy: 98.47%
Grounded answers: 97.37%
Correct refusals: 100.0%
Error rate: 0.0%

| Category | n | Accuracy |
|---|---|---:|
| normal | 26 | 96.15% |
| paraphrased | 20 | 95% |
| noisy | 15 | 100% |
| multilingual | 15 | 100% |
| off_topic | 25 | 100% |
| unanswerable | 15 | 100% |
| adversarial | 15 | 100% |

### Latency — RAG only (query → answer) — fast tier (MSMARCO-XI, n=120)
P50: 68 ms
P70: 71 ms
P100: 131 ms

| Stage | P50 |
|---|---:|
| Query processing | 0.04 ms |
| Embedding | 8.55 ms |
| Dense retrieval | 20.52 ms |
| BM25 | 5.84 ms |
| Fusion | 0.03 ms |
| Reranking | 10.47 ms |
| Generation | 10.52 ms |
| Guardrail | 10.45 ms |
| Total | 68 ms |

### Latency — LLM tier (MSMARCO-XI, n=25; local Qwen2.5 model, CPU)
P50: 850 ms
P70: 965 ms
P100: 6114 ms

The first query after load pays the model warm-up (≈30–40 s); the p100 outlier is the
model load start. LLM generation dominates at ~790 ms P50. The LLM tier is used when the
extractive (fast) tier cannot reach high confidence.

### Latency — End-to-end voice (voice → STT → RAG → answer)
P50: Not measured in this local environment
P70: Not measured in this local environment
P100: Not measured in this local environment

Measured by `python -m benchmarks.run_voice_latency_bench` once `SARVAM_API_KEY` is set
and audio samples exist under `data/voice_samples/` — it reports RAG-only, STT, and
end-to-end P50/P70/P100 separately and writes an honest "not measured" report otherwise.

### Guardrails
Grounded answers: 97.37%
Correct refusals: 100.0%

Refusals cover off-topic queries, adversarial/prompt-injection attempts, low-support
extractive answers, and temporally-unanswerable questions (e.g. future-dated weather
forecasts or exact future event timing), which a static corpus cannot know.

## Example result

A local backend call returned:

- Query: "What is the capital of France?"
- Answer: "Paris is the capital of France."
- Grounded: `true`
- Confidence: `0.94`

## Known limits

This repository is a local working prototype. The challenge spec requires a much larger offline dataset pipeline, actual STT provider integration, full latency benchmarking across a bigger evaluation set, and deployment/delivery artifacts that are not yet included in this environment.

## Run locally

Backend:

```bash
cd backend
pip install -r requirements.txt          # includes the ML/retrieval stack
cp .env.example .env                     # optional; all settings have defaults
# Build the offline index (data/passages.jsonl must exist under data/)
python -m backend.app.ingestion.embed_and_index   # optional limit: ... 25000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

The default port the frontend calls is `8001`; set it in `frontend/src/App.jsx`
or run uvicorn on `--port 8001`.

Benchmarking:

```bash
cd backend
python -m benchmarks.run_latency_bench        # RAG-only P50/P70/P100 + stage table
python -m benchmarks.run_quality_bench        # Recall@5/@10, MRR, behavior
python -m benchmarks.run_voice_latency_bench  # voice → STT → RAG (needs key + samples)
```

## Deployment

`backend/Dockerfile` + `render.yaml` and `frontend/vercel.json` are ready to use.
Follow `DEPLOYMENT.md` step by step; set `VITE_API_BASE` to the deployed backend URL.

## Submission checklist

From the HH Goa 2026 Task 2 master prompt — no resubmissions allowed, so verify each:

- [x] GitHub repo with README + real measured numbers
- [ ] Live deployed link (backend on Render, frontend on Vercel — see `DEPLOYMENT.md`)
- [ ] Video 1: 90s team/process video (process, not product)
- [ ] Video 2: end-to-end demo video (normal, paraphrase, off-topic refusal,
      grounding/citations, multilingual if implemented)
- [ ] Both videos posted on Instagram, X, and LinkedIn by every team member,
      tagged **#RAGInGoa**, at least one Instagram account public
- [ ] Submission form filled: https://forms.gle/MNvCjcv23Hn2Eeu58

## Notes

The project prioritizes working infrastructure and a believable demo experience over a fully production-scale dataset pipeline. The implemented flow is consistent with the challenge architecture and is ready for the next stage of the full submission build.
