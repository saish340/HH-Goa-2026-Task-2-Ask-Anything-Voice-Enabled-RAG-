"""Guardrail #3 — post-hoc grounding verification.

Checks the generated answer against the retrieved context and labels it
SUPPORTED / UNSUPPORTED. Blends lexical containment (significant answer tokens
present in context) with embedding similarity between answer and context.
"""

from __future__ import annotations

import re
from typing import Sequence

from backend.app.config import GROUNDING_MIN

STOPWORDS = {
    "a", "an", "the", "of", "to", "and", "is", "are", "was", "were", "in", "on",
    "at", "it", "its", "for", "with", "that", "this", "or", "as", "by", "from",
    "be", "do", "does", "did", "have", "has", "had", "not", "no", "what", "which",
}


def _significant_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[\w']+", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 1}


def grounding_score(answer: str, retrieved_texts: Sequence[str]) -> float:
    if not answer or not retrieved_texts:
        return 0.0
    context = " ".join(retrieved_texts)
    ctx_tokens = _significant_tokens(context)
    ans_tokens = _significant_tokens(answer)
    if not ans_tokens or not ctx_tokens:
        return 0.0

    lexical = len(ans_tokens & ctx_tokens) / len(ans_tokens)
    semantic = _semantic_similarity(answer, context)
    return round(min(max(0.55 * lexical + 0.45 * semantic, 0.0), 1.0), 3)


def _semantic_similarity(answer: str, context: str) -> float:
    try:
        from backend.app.retrieval.embeddings import embed_texts

        vecs = embed_texts([answer, context], batch_size=2)
        if len(vecs) < 2:
            return 0.0
        a, c = vecs[0], vecs[1]
        return float(a @ c)
    except Exception:
        return 0.0


def groundedness_check(answer: str, retrieved_texts: Sequence[str]) -> tuple[bool, float, str]:
    """Returns (supported_bool, score, label)."""
    score = grounding_score(answer, retrieved_texts)
    supported = score >= GROUNDING_MIN
    label = "SUPPORTED" if supported else "UNSUPPORTED"
    return supported, score, label