# Latency report — RAG only (query → answer)

## fast_tier tier

Test queries: 120
P50: 70.0 ms / P70: 73.0 ms / P100: 101.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.97 |
| dense | 21.135 |
| bm25 | 6.065 |
| fusion | 0.03 |
| rerank | 8.21 |
| generation | 10.86 |
| guardrail | 10.5 |

## llm_tier tier

Test queries: 25
P50: 795.0 ms / P70: 981.4 ms / P100: 5507.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.62 |
| dense | 20.44 |
| bm25 | 6.36 |
| fusion | 0.03 |
| rerank | 8.11 |
| generation | 743.86 |
| guardrail | 10.54 |
