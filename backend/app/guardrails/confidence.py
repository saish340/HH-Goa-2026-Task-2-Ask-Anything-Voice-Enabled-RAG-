from __future__ import annotations


def compute_confidence(scores: list[float], retrieved_count: int) -> float:
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    return round(min(max(avg, 0.0), 1.0), 3)
