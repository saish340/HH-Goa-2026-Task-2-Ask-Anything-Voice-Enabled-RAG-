"""Guardrail #2 — retrieval confidence threshold.

Combines dense cosine scores, BM25 magnitude, and grounding into a 0..1
confidence. Below ``CONFIDENCE_MIN`` (and unsupported) the orchestrator refuses.
"""

from __future__ import annotations

from typing import Optional


def compute_confidence(
    dense_cosines: list[float],
    bm25_score: Optional[float] = None,
    grounded: bool = False,
) -> float:
    if not dense_cosines:
        return 0.0
    top = sorted(dense_cosines, reverse=True)[:3]
    dense_part = sum(top) / len(top)
    lex_part = min(1.0, (bm25_score or 0.0) / 8.0)
    base = 0.58 * dense_part + 0.32 * lex_part + 0.10 * float(grounded)
    return round(min(max(base, 0.0), 1.0), 3)


def below_threshold(confidence: float, threshold: float) -> bool:
    return confidence < threshold