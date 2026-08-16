"""Guardrail #1 — off-topic detection.

A query is considered off-topic when the best retrieved passage has weak
dense similarity to the query (below ``OFF_TOPIC_COSINE_THRESHOLD``) or when
retrieval returns nothing at all. The score used here is the raw FAISS cosine
similarity between the query embedding and the top chunk embedding.
"""

from __future__ import annotations

from backend.app.config import OFF_TOPIC_COSINE_THRESHOLD


def best_similarity(dense_hits: list[tuple[int, float]]) -> float:
    if not dense_hits:
        return 0.0
    return max(score for _, score in dense_hits)


def is_off_topic(dense_hits: list[tuple[int, float]], retrieved_count: int) -> bool:
    if retrieved_count == 0 or not dense_hits:
        return True
    return best_similarity(dense_hits) < OFF_TOPIC_COSINE_THRESHOLD