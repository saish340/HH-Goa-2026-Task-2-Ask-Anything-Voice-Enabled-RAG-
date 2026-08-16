"""Query normalization / lightweight rewrite step."""

from __future__ import annotations

import re


def normalize_query(query: str) -> str:
    """Clean STT-style artifacts: filler words, dup whitespace, stray punctuation."""
    if not query:
        return ""
    q = query.strip()
    q = re.sub(r"\s+", " ", q)
    q = re.sub(r"\b(?:uh|um|hmm|like|ya know|ah|er)\b", " ", q, flags=re.IGNORECASE)
    q = re.sub(r"([?.,!;:])", r" \1", q)
    q = re.sub(r"\s+", " ", q).strip()
    q = re.sub(r"\.(?=\s|$)", "", q).strip()
    return q[:512]


def detect_language(query: str) -> str:
    """Heuristic script-based language tag for routing STT/RAG behavior."""
    devanagari = bool(re.search(r"[\u0900-\u097F]", query))
    arabic = bool(re.search(r"[\u0600-\u06FF]", query))
    bengali = bool(re.search(r"[\u0980-\u09FF]", query))
    if devanagari:
        return "hi"
    if arabic:
        return "ur"
    if bengali:
        return "bn"
    return "en"