"""Query → chunk-strategy routing.

Short factual queries hit the sentence-level chunks, conceptual questions hit
the semantic chunks, verbose/contextual queries hit the sliding-window chunks,
and everything else falls through to a cross-strategy fusion.
"""

from __future__ import annotations

import re
from typing import Optional

from backend.app.config import SHORT_QUERY_WORD_MAX

CONCEPT_TERMS = {
    "why", "how", "explain", "difference", "compare", "comparison", "relation",
    "relationship", "impact", "effect", "affect", "consequence", "cause",
    "mechanism", "process", "analyze", "analysis", "summary", "summarize",
    "contrast", "definition", "context",
}
FACTUAL_TERMS = {
    "what", "who", "when", "where", "which", "capital", "located", "named",
    "is", "are", "born", "founded", "city", "country", "person", "date",
}


def _words(query: str) -> list[str]:
    return re.findall(r"\b[\w']+\b", query.lower())


def route_strategy(query: str) -> str:
    """Pick the chunk strategy index to search, or "all" to fuse every strategy."""
    query = (query or "").strip()
    words = _words(query)
    if not words:
        return "all"

    if len(words) <= SHORT_QUERY_WORD_MAX:
        if set(words) & FACTUAL_TERMS:
            return "sentence"
        if set(words) & CONCEPT_TERMS:
            return "semantic"
        return "sentence"

    if set(words) & CONCEPT_TERMS:
        return "semantic"
    if len(words) > 30:
        return "sliding_window"
    return "all"


def explain_strategy(query: str) -> Optional[str]:
    strategy = route_strategy(query)
    return None if strategy == "all" else strategy