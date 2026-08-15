from __future__ import annotations

from statistics import mean

from backend.app.harness.orchestrator import run_query

TEST_QUERIES = [
    ("What is the capital of France?", True),
    ("Which city is the capital of India?", True),
    ("What temperature does water boil at?", True),
    ("How to bake a cake in the moon?", False),
    ("Who is the president of the United States?", False),
]


def benchmark() -> dict:
    results = []
    for query, expected_supported in TEST_QUERIES:
        response = run_query(query)
        correct = bool(response["grounded"]) == expected_supported
        results.append({
            "query": query,
            "expected": expected_supported,
            "grounded": response["grounded"],
            "correct": correct,
            "latency_ms": response["latency_ms"],
        })

    accuracy = mean(1.0 if item["correct"] else 0.0 for item in results)
    grounded_rate = mean(1.0 if item["grounded"] else 0.0 for item in results if item["expected"])
    return {
        "queries": len(results),
        "accuracy": round(accuracy * 100, 2),
        "grounded_rate": round(grounded_rate * 100, 2) if results else 0,
        "latencies": [item["latency_ms"] for item in results],
    }


if __name__ == "__main__":
    print(benchmark())
