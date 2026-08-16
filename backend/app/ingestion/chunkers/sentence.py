from __future__ import annotations

import math
import re
from typing import Any, Callable, Dict, List, Optional

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
QUOTED_ABBREV = re.compile(r"\b([A-Za-z]\.)+$")


def split_sentences(text: str) -> List[str]:
    """Split text into sentences, guarding simple abbreviations."""
    if not text:
        return []
    parts = SENTENCE_SPLIT_RE.split(text.strip())
    cleaned: List[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Merge fragments that end with a detached abbreviation like "U.S." or "e.g."
        if cleaned and not cleaned[-1].endswith((".", "!", "?")):
            cleaned[-1] = f"{cleaned[-1]} {part}"
        else:
            cleaned.append(part)
    return cleaned


def _token_count(text: str) -> int:
    return max(1, len(text.split()))


def sentence_chunker(
    text: str,
    document_id: str = "doc-1",
    language: str = "en",
    max_chars: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Sentence-level chunking — one chunk per sentence with metadata."""
    if not text or not text.strip():
        return []
    chunks: List[Dict[str, Any]] = []
    for idx, sentence in enumerate(split_sentences(text), start=1):
        if max_chars and len(sentence) > max_chars:
            # Split oversized sentences into word windows.
            words = sentence.split()
            for wpos, start in enumerate(range(0, len(words), 40), start=1):
                piece = " ".join(words[start : start + 40])
                chunks.append({
                    "chunk_id": f"{document_id}-sentence-{idx}-{wpos}",
                    "document_id": document_id,
                    "chunk_strategy": "sentence",
                    "position": idx,
                    "token_count": _token_count(piece),
                    "language": language,
                    "text": piece,
                    "metadata": {"sentence_index": idx},
                })
            continue
        chunks.append({
            "chunk_id": f"{document_id}-sentence-{idx}",
            "document_id": document_id,
            "chunk_strategy": "sentence",
            "position": idx,
            "token_count": _token_count(sentence),
            "language": language,
            "text": sentence,
            "metadata": {"sentence_index": idx, "char_count": len(sentence)},
        })
    return chunks