from __future__ import annotations

import math
import re
from typing import Any, Callable, Dict, List, Optional

from backend.app.ingestion.chunkers.sentence import split_sentences


def _token_count(text: str) -> int:
    return max(1, len(text.split()))


def _key_terms(text: str) -> List[str]:
    tokens = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
    stop = {"the", "and", "of", "to", "a", "in", "on", "for", "is", "are", "it", "with", "by", "as", "was", "were", "an", "at", "or", "this", "that"}
    return sorted(t for t in tokens if len(t) > 1 and t not in stop)


def semantic_chunker(
    text: str,
    document_id: str = "doc-1",
    language: str = "en",
    embed_fn: Optional[Callable[[str], List[float]]] = None,
    similarity_threshold: float = 0.55,
    max_chunk_sentences: int = 4,
) -> List[Dict[str, Any]]:
    """Group consecutive sentences into semantic chunks.

    When ``embed_fn`` is provided, sentences are merged based on embedding
    cosine similarity with the running chunk (true semantic grouping).
    Otherwise a deterministic keyword-overlap fallback is used.
    """
    if not text or not text.strip():
        return []
    sentences = split_sentences(text)
    if not sentences:
        return []

    embeddings: List[List[float]] = []
    if embed_fn is not None:
        embeddings = [embed_fn(s) for s in sentences]
    else:
        embeddings = [None] * len(sentences)

    groups: List[List[str]] = [[sentences[0]]]
    group_rep: List[List[float]] = [embeddings[0] if embeddings[0] is not None else None]

    def _cos(a: List[float], b: List[float]) -> float:
        if a is None or b is None:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(y * y for y in b)) or 1.0
        return dot / (na * nb)

    def _overlap_score(s1: List[str], s2a: List[str]) -> float:
        k1, k2 = set(_key_terms(" ".join(s1))), set(_key_terms(" ".join(s2a)))
        if not k1 or not k2:
            return 0.0
        return len(k1 & k2) / len(k1 | k2)

    for i in range(1, len(sentences)):
        group = groups[-1]
        if len(group) >= max_chunk_sentences:
            groups.append([sentences[i]])
            group_rep.append(embeddings[i])
            continue
        rep = group_rep[-1]
        if embeddings[i] is not None and rep is not None:
            similar = _cos(embeddings[i], rep)
        else:
            similar = _overlap_score(group, [sentences[i]])
        if similar >= similarity_threshold:
            group.append(sentences[i])
        else:
            groups.append([sentences[i]])
            group_rep.append(embeddings[i])

    chunks: List[Dict[str, Any]] = []
    cursor = 0
    for gidx, group in enumerate(groups):
        chunk_text = " ".join(group)
        start, end = cursor, cursor + len(group)
        cursor = end
        chunks.append({
            "chunk_id": f"{document_id}-semantic-{gidx}",
            "document_id": document_id,
            "chunk_strategy": "semantic",
            "position": gidx,
            "token_count": _token_count(chunk_text),
            "language": language,
            "text": chunk_text,
            "key_terms": _key_terms(chunk_text),
            "metadata": {"sentence_span": [start, end]},
        })
    return chunks