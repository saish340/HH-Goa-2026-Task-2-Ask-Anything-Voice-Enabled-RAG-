"""Query normalization / lightweight rewrite step."""

from __future__ import annotations

import re
from datetime import date

_FUTURE_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_FUTURE_WORDS = {
    "tomorrow", "tonight", "next week", "next month", "next year",
    "forecast", "predict", "prediction", "predictions", "future",
}
_PREDICT_VERBS = {
    "will", "going to", "gonna", "would",
}
_WEATHER_TERMS = {
    "weather", "temperature", "temperatures", "rain", "rainfall", "snow",
    "humid", "humidity", "forecast", "forecasted",
}


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


def _words(query: str) -> set[str]:
    return set(re.findall(r"\b[\w']+\b", query.lower()))


def is_temporal_unanswerable(query: str) -> bool:
    """True when the query asks the KB to predict future events it cannot know.

    Static, retrieval-based answers can only describe recorded facts. Queries that
    request a future-dated forecast/condition or an exact future occurrence are
    denied up front instead of scraped from an unrelated passage.
    """
    q = (query or "").strip().lower()
    if not q:
        return False

    future_year = None
    for m in _FUTURE_YEAR.finditer(q):
        try:
            if int(m.group()) > date.today().year:
                future_year = int(m.group())
                break
        except ValueError:
            continue

    has_predict = any(w in q for w in _FUTURE_WORDS)
    has_verb = any(v in q for v in _PREDICT_VERBS)
    has_weather = bool(set(q.split()) & _WEATHER_TERMS)

    # A forecast request pinned to a future frame (explicit year, or an
    # upcoming "next/tonight/tomorrow") is not answerable from a corpus.
    if has_weather and has_verb and (future_year is not None or has_predict):
        return True

    # An exact-future-occurrence question ("when will X happen exactly")
    # cannot be established from recorded history.
    if "when" in q and "will" in q and "exactly" in q:
        return True

    # A bare request for a prediction in an explicit future year.
    if future_year is not None and has_predict:
        return True

    return False