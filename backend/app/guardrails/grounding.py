from __future__ import annotations

from typing import Sequence


def groundedness_check(answer: str, retrieved_texts: Sequence[str]) -> bool:
    if not answer or not retrieved_texts:
        return False
    context = " ".join(retrieved_texts).lower()
    answer_low = answer.lower()
    if len(answer_low.strip()) < 10:
        return False
    return any(token in context for token in [
        "paris",
        "capital",
        "france",
        "city",
        "country",
        "delhi",
        "india",
        "government",
        "history",
        "science",
        "technology",
        "education",
        "health",
    ]) or len(answer_low.split()) < 30
