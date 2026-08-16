# Quality report

Dataset: MSMARCO-XI

## Retrieval
Test queries: 150
Recall@5: 64.67%
Recall@10: 79.33%
MRR: 0.359

## Guardrails / behavior
Test queries: 131
Overall accuracy: 93.13%
Grounded answers: 90.79%
Correct refusals: 96.36%
Error rate: 0.0%

| Category | n | Accuracy |
|---|---|---|
| normal | 26 | 92.31% |
| paraphrased | 20 | 95.0% |
| noisy | 15 | 100.0% |
| multilingual | 15 | 73.33% |
| off_topic | 25 | 100.0% |
| unanswerable | 15 | 86.67% |
| adversarial | 15 | 100.0% |