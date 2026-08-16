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
    # CJK: Han + Kana share an encoding block; treat Hiragana/Katakana as
    # Japanese and pure Han characters as Chinese.
    hiragana = bool(re.search(r"[\u3040-\u309F]", query))
    katakana = bool(re.search(r"[\u30A0-\u30FF]", query))
    han = bool(re.search(r"[\u4E00-\u9FFF]", query))
    if devanagari:
        return "hi"
    if arabic:
        return "ur"
    if bengali:
        return "bn"
    if hiragana or katakana:
        return "ja"
    if han:
        return "zh"
    return "en"