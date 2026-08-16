# Quality report

Dataset: MSMARCO-XI

## Retrieval
Test queries: 150
Recall@5: 64.67%
Recall@10: 79.33%
MRR: 0.359

## Guardrails / behavior
Test queries: 131
Overall accuracy: 84.73%
Grounded answers: 93.42%
Correct refusals: 72.73%
Error rate: 0.0%

| Category | n | Accuracy |
|---|---|---|
| normal | 26 | 96.15% |
| paraphrased | 20 | 100.0% |
| noisy | 15 | 100.0% |
| multilingual | 15 | 73.33% |
| off_topic | 25 | 76.0% |
| unanswerable | 15 | 53.33% |
| adversarial | 15 | 86.67% |