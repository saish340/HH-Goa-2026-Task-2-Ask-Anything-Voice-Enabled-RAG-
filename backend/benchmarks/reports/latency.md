# Latency report — RAG only (query → answer)

## fast_tier tier

Test queries: 120
P50: 68.0 ms / P70: 71.0 ms / P100: 131.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.545 |
| dense | 20.52 |
| bm25 | 5.84 |
| fusion | 0.03 |
| rerank | 10.465 |
| generation | 10.515 |
| guardrail | 10.45 |

## llm_tier tier

Test queries: 25
P50: 850.0 ms / P70: 965.4 ms / P100: 6114.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.6 |
| dense | 19.48 |
| bm25 | 6.17 |
| fusion | 0.03 |
| rerank | 9.92 |
| generation | 790.21 |
| guardrail | 10.56 |
