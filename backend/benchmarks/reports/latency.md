# Latency report — RAG only (query → answer)

## fast_tier tier

Test queries: 120
P50: 67.0 ms / P70: 70.0 ms / P100: 100.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.765 |
| dense | 20.61 |
| bm25 | 5.755 |
| fusion | 0.03 |
| rerank | 9.875 |
| generation | 10.47 |
| guardrail | 10.605 |

## llm_tier tier

Test queries: 25
P50: 845.0 ms / P70: 987.2 ms / P100: 6123.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 8.81 |
| dense | 19.53 |
| bm25 | 5.76 |
| fusion | 0.03 |
| rerank | 9.84 |
| generation | 786.26 |
| guardrail | 10.12 |
