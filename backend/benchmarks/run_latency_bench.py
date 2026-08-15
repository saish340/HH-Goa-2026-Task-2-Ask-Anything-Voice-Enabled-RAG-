from __future__ import annotations

import statistics
import time

from backend.app.harness.orchestrator import run_query

QUERIES = [
    "What is the capital of France?",
    "Which city is the capital of India?",
    "What temperature does water boil at?",
    "How to bake a cake in the moon?",
    "What is the capital of France?",
    "Which city is the capital of India?",
    "What temperature does water boil at?",
    "How to bake a cake in the moon?",
]


def benchmark() -> dict:
    latencies = []
    for query in QUERIES:
        start = time.perf_counter()
        run_query(query)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)

    return {
        "test_queries": len(latencies),
        "p50": round(statistics.median(latencies), 2),
        "p70": round(statistics.quantiles(latencies, n=10)[6], 2) if len(latencies) >= 7 else round(max(latencies), 2),
        "p100": round(max(latencies), 2),
        "mean": round(statistics.mean(latencies), 2),
        "latencies_ms": [round(v, 2) for v in latencies],
    }


if __name__ == "__main__":
    print(benchmark())
