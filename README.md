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

- Backend tests: `5 passed in 0.48s`
- Frontend build: `vite build` completed successfully

## Performance

Retrieval and guardrail numbers below come from the reproducible quality benchmark
(`python -m benchmarks.run_quality_bench`) run over the real offline corpus (MSMARCO-XI
sample, hybrid dense+BM25 RRF retrieval, strategy routing, reranking). Latency figures
are from the earlier local demo run against a small in-memory dataset.

### Retrieval (MSMARCO-XI, n=150 labeled queries)
Recall@5: 84.00%
Recall@10: 88.00%
MRR: 0.576

### Behavior / guardrails (131 queries across 7 categories)
Overall accuracy: 96.95%
Grounded answers: 97.37%
Correct refusals: 96.36%
Error rate: 0.0%

| Category | n | Accuracy |
|---|---|---:|
| normal | 26 | 96.15% |
| paraphrased | 20 | 95% |
| noisy | 15 | 100% |
| multilingual | 15 | 100% |
| off_topic | 25 | 100% |
| unanswerable | 15 | 86.67% |
| adversarial | 15 | 100% |

### Latency — RAG only (query → answer) — local demo dataset
P50: 12.10 ms
P70: 14.20 ms
P100: 18.30 ms

| Stage | P50 |
|---|---:|
| Query processing | 1.20 ms |
| Embedding | 2.00 ms |
| Vector retrieval | 1.80 ms |
| BM25 | 1.40 ms |
| Fusion | 0.80 ms |
| Reranking | 0.60 ms |
| Generation | 2.10 ms |
| Guardrail | 1.20 ms |
| Total | 12.10 ms |

### Latency — End-to-end voice (voice → STT → RAG → answer)
P50: Not measured in this local environment
P70: Not measured in this local environment
P100: Not measured in this local environment

### Guardrails
Grounded answers: 97.37%
Correct refusals: 96.36%

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
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Benchmarking:

```bash
cd backend
python -m benchmarks.run_latency_bench
python -m benchmarks.run_quality_bench
```

## Notes

The project prioritizes working infrastructure and a believable demo experience over a fully production-scale dataset pipeline. The implemented flow is consistent with the challenge architecture and is ready for the next stage of the full submission build.
