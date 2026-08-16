# Latency report — RAG only (query → answer)

## fast_tier tier

Test queries: 120
P50: 73.0 ms / P70: 77.0 ms / P100: 136.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.04 |
| embedding | 9.54 |
| dense | 21.165 |
| bm25 | 6.415 |
| fusion | 0.03 |
| rerank | 8.935 |
| generation | 11.69 |
| guardrail | 11.135 |

## llm_tier tier

Test queries: 25
P50: 890.0 ms / P70: 1048.6 ms / P100: 6092.0 ms

| Stage | P50 (ms) |
|---|---|
| query_processing | 0.05 |
| embedding | 8.92 |
| dense | 20.8 |
| bm25 | 6.61 |
| fusion | 0.03 |
| rerank | 8.35 |
| generation | 837.26 |
| guardrail | 10.96 |
