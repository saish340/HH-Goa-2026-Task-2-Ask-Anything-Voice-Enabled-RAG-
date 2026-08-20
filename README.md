# HH Goa 2026 — Ask Anything (Voice-Enabled RAG)

This project is a local working prototype for the HH Goa 2026 Task 2 challenge. It includes a FastAPI backend, a hybrid retrieval flow, guardrails, and a dark HH Goa–inspired frontend.

## What is implemented

- FastAPI backend with a query endpoint at `/api/ask`
- Dense + BM25 hybrid retrieval with Reciprocal Rank Fusion
- Multi-strategy chunking layer with sentence, semantic, and sliding-window chunkers
- Guardrails for off-topic and low-support rejection
- Structured JSON response with query, retrieved chunks, confidence, grounded flag, and latency
- HH Goa themed React UI with voice-first hero, status line, and answer card
- Multilingual text + voice: Hindi / Marathi / Urdu queries answer correctly in their own
  script (bounded curated corpus + Unicode-aware lexical retrieval and grounding), with an
  in-UI language selector that drives both STT and RAG

## Project structure

- `backend/app` — core app and API logic
- `backend/app/tests` — validation tests
- `backend/app/ingestion` — corpus build (`ingest.py`), multilingual augmentation
  (`multilingual.py`), and offline index build (`embed_and_index.py`)
- `backend/benchmarks` — latency and quality scripts
- `frontend` — React + Vite app

## Verification

Fresh local validation performed:

- Backend tests: `22 passed`
- Frontend build: `vite build` completed successfully

## Performance

Retrieval and guardrail numbers below come from the reproducible quality benchmark
(`python -m benchmarks.run_quality_bench`) run over the real offline corpus (MSMARCO-XI
sample + curated hi/mr/ur augmentation, hybrid dense+BM25 RRF retrieval, strategy routing,
reranking). Latency figures are from `python -m benchmarks.run_latency_bench` on the same
corpus. Both were re-run and regenerated on the machine this repo was built on
(13th-Gen Intel Core i7-13700HX, 24 threads, CPU-only inference).

### Retrieval (MSMARCO-XI, n=150 labeled queries)
Recall@5: 83.33%
Recall@10: 87.33%
MRR: 0.573

### Behavior / guardrails (131 queries across 7 categories)
Overall accuracy: 98.47%
Grounded answers: 97.37%
Correct refusals: 100.0%
Error rate: 0.0%

| Category | n | Accuracy |
|---|---:|---:|
| normal | 26 | 96.15% |
| paraphrased | 20 | 95.00% |
| noisy | 15 | 100% |
| multilingual | 15 | 100% |
| off_topic | 25 | 100% |
| unanswerable | 15 | 100% |
| adversarial | 15 | 100% |

### Latency — RAG only (query → answer) — fast tier (n=120)
P50: 69 ms
P70: 72 ms
P100: 145 ms

| Stage | P50 |
|---|---:|
| Query processing | 0.04 ms |
| Embedding | 8.89 ms |
| Dense retrieval | 21.02 ms |
| BM25 | 5.90 ms |
| Fusion | 0.03 ms |
| Reranking | 10.09 ms |
| Generation | 10.81 ms |
| Guardrail | 10.44 ms |
| Total | 69 ms |

All three percentiles are comfortably under the 200 ms P100 target of the challenge spec.

### Latency — LLM tier (n=25; local Qwen2.5-0.5B, CPU)
P50: 815 ms
P70: 949 ms
P100: 5521 ms

LLM generation dominates at ~762 ms P50. The LLM tier is opt-in (`tier: "llm"`);
the default fast (extractive) tier is what the voice demo and benchmark targets use.
The first LLM call after process start additionally pays the model warm-up; the RAG
index/encoder/reranker are preloaded at backend startup (outer-app lifespan), so the
very first `/api/ask` no longer bears the ~80 s cold start.

### Latency — End-to-end voice (voice → STT → RAG → answer)
P50: Not measured in this local environment
P70: Not measured in this local environment
P100: Not measured in this local environment

Measured by `python -m benchmarks.run_voice_latency_bench` once `SARVAM_API_KEY` is set
and audio samples exist under `data/voice_samples/` — it reports RAG-only, STT, and
end-to-end P50/P70/P100 separately and writes an honest "not measured" report otherwise.
STT is an out-of-process Sarvam network call whose latency is outside the RAG <200 ms claim.

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

In Hindi the same path answers in-script, e.g. query "भारत की राजधानी कौन सा शहर है?" →
"भारत की राजधानी नई दिल्ली है।" (grounded, confidence 0.84).

## Multilingual support

- The offline corpus is English-first (MSMARCO-XI sample). The bundled snapshot
  (`urdval.parquet`) is an English→Urdu machine-translation file with no Hindi/Marathi
  content, so `backend/app/ingestion/multilingual.py` appends a small, hand-verified set
  of canonical-fact passages in Hindi, Marathi, and Urdu (17 passages). Rebuild the index
  with `embed_and_index` afterwards.
- Lexical retrieval (BM25), extractive generation, and post-hoc grounding are now
  Unicode-aware (`\w` tokenization incl. Devanagari/Arabic; sentence splitting handles the
  Devanagari danda): same-script queries match same-script chunks and answers are grounded
  by token containment, not just embedding similarity.
- Dense retrieval uses the multilingual `paraphrase-multilingual-MiniLM-L12-v2` encoder, so
  cross-lingual matching against English passages also works. The MS-MARCO cross-encoder
  reranker stays gated to Latin-script queries (it is English-only by construction).
- The frontend voice flow has a language selector (Auto / English / हिन्दी / मराठी / اردو)
  that drives both the Sarvam STT language code and the RAG language hint.

## Known limits

This is a local working prototype: STT is a live Sarvam API call and needs `SARVAM_API_KEY`
(+ `data/voice_samples/` to benchmark end-to-end voice latency), the deployment is not yet
live (see checklist below), and multilingual coverage is intentionally bounded to the
curated canonical-fact passages rather than a fully machine-translated corpus. The RAG-only
latency and quality numbers above are measured, reproducible, and regenerated by the bench
scripts.

## Run locally

Backend:

```bash
cd backend
pip install -r requirements.txt          # includes the ML/retrieval stack
cp .env.example .env                     # optional; all settings have defaults
# Build the offline index (data/passages.jsonl must exist under data/)
python -m backend.app.ingestion.ingest        # rebuild passages.jsonl + eval queries
python -m backend.app.ingestion.multilingual  # append curated hi/mr/ur canonical passages
python -m backend.app.ingestion.embed_and_index   # optional limit: ... 25000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

The default port the frontend calls is `8001`; set `VITE_API_BASE` in
`frontend/.env` or run uvicorn on `--port 8001`.

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
      grounding/citations, multilingual — unimplemented. Multilingual is implemented and
      benchmarked at 100% on the curated hi/mr/ur set; the video should demo it)
- [ ] Both videos posted on Instagram, X, and LinkedIn by every team member,
      tagged **#RAGInGoa**, at least one Instagram account public
- [ ] Submission form filled: https://forms.gle/MNvCjcv23Hn2Eeu58

## Notes

The project prioritizes working infrastructure and a believable demo experience over a fully production-scale dataset pipeline. The implemented flow is consistent with the challenge architecture and is ready for the next stage of the full submission build.
