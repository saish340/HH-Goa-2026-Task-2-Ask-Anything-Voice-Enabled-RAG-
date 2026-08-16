# Latency report — RAG only (query → answer)

## fast_tier tier

Test queries: 120
P50: 67.0 ms / P70: 71.0 ms / P100: 102.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.76 |
| dense | 20.575 |
| bm25 | 5.54 |
| fusion | 0.03 |
| rerank | 9.87 |
| generation | 10.61 |
| guardrail | 10.64 |

## llm_tier tier

Test queries: 25
P50: 859.0 ms / P70: 990.8 ms / P100: 4430.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 9.1 |
| dense | 20.48 |
| bm25 | 6.33 |
| fusion | 0.03 |
| rerank | 9.51 |
| generation | 800.52 |
| guardrail | 10.52 |
