from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple


def reciprocal_rank_fusion(
    dense_hits: Sequence[Tuple[int, float]],
    bm25_hits: Sequence[Tuple[int, float]],
    k: int = 60,
) -> List[Tuple[int, float]]:
    fused_scores: dict[int, float] = {}
    for rank, (idx, _) in enumerate(dense_hits, start=1):
        fused_scores[idx] = fused_scores.get(idx, 0.0) + 1.0 / (k + rank)
    for rank, (idx, _) in enumerate(bm25_hits, start=1):
        fused_scores[idx] = fused_scores.get(idx, 0.0) + 1.0 / (k + rank)
    ranked = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)
    return [(idx, score) for idx, score in ranked]
