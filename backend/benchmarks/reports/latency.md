# Latency report — RAG only (query → answer)

## fast_tier tier

Test queries: 120
P50: 69.0 ms / P70: 72.0 ms / P100: 145.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.885 |
| dense | 21.02 |
| bm25 | 5.895 |
| fusion | 0.03 |
| rerank | 10.09 |
| generation | 10.81 |
| guardrail | 10.44 |

## llm_tier tier

Test queries: 25
P50: 815.0 ms / P70: 949.0 ms / P100: 5521.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.36 |
| dense | 19.28 |
| bm25 | 6.03 |
| fusion | 0.03 |
| rerank | 9.75 |
| generation | 761.89 |
| guardrail | 10.38 |
