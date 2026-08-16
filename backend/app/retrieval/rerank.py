"""Lightweight cross-encoder reranker.

Gated behind a latency check in the orchestrator: it runs on a short list of
candidates when the fast path (dense + BM25 + fusion) is still cheap, and is
skipped entirely when doing so would blow the sub-200ms budget.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from backend.app.config import DEVICE, RERANK_MODEL

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(RERANK_MODEL, device=DEVICE, max_length=384)
    return _model


def rerank(
    query: str,
    candidates: List[Tuple[int, str]],
    top_k: int,
) -> List[Tuple[int, float]]:
    """Score (position, text) candidates with the cross-encoder."""
    if not candidates:
        return []
    model = _get_model()
    pairs = [(query, text) for _, text in candidates]
    scores = model.predict(pairs, batch_size=32, show_progress_bar=False)
    if getattr(scores, "ndim", 0) == 1 and len(scores) > 0:
        scores = scores.tolist()
    else:
        scores = list(np.asarray(scores, dtype=float).reshape(-1))

    ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
    return [(pos, float(score)) for (pos, _), score in ranked[:top_k]]


def warmup() -> None:
    _get_model()