from __future__ import annotations

import re
from typing import Sequence

STOPWORDS = {"a", "an", "the", "to", "in", "on", "of", "for", "how", "what", "when", "where", "why", "who", "which", "is", "are", "do", "does", "did", "it", "its", "be", "was", "were"}


def _tokens(text: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return {token for token in cleaned.split() if token and token not in STOPWORDS}


def is_off_topic(query: str, retrieved_chunks: Sequence[str]) -> bool:
    if not retrieved_chunks:
        return True

    query_tokens = _tokens(query)
    chunk_tokens = _tokens(" ".join(retrieved_chunks))
    overlap = query_tokens & chunk_tokens
    return len(overlap) == 0
