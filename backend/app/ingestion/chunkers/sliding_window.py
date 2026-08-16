from __future__ import annotations

import re
from typing import Any, Dict, List

from backend.app.ingestion.chunkers.sentence import split_sentences


def sliding_window_chunker(
    text: str,
    window_size: int = 25,
    stride: int = 10,
    document_id: str = "doc-1",
    language: str = "en",
) -> List[Dict[str, Any]]:
    """Word-level sliding-window chunking with overlap for context preservation."""
    if not text or not text.strip():
        return []
    tokens = re.findall(r"\S+", text)
    if len(tokens) <= window_size:
        stripped = " ".join(tokens).strip()
        if not stripped:
            return []
        return [{
            "chunk_id": f"{document_id}-window-0",
            "document_id": document_id,
            "chunk_strategy": "sliding_window",
            "position": 0,
            "token_count": len(tokens),
            "language": language,
            "text": stripped,
            "metadata": {"window_index": 0, "token_start": 0, "token_end": len(tokens)},
        }]

    chunks: List[Dict[str, Any]] = []
    position = 0
    start = 0
    while start < len(tokens):
        end = min(start + window_size, len(tokens))
        snippet = " ".join(tokens[start:end]).strip()
        chunks.append({
            "chunk_id": f"{document_id}-window-{position}",
            "document_id": document_id,
            "chunk_strategy": "sliding_window",
            "position": position,
            "token_count": len(snippet.split()),
            "language": language,
            "text": snippet,
            "metadata": {
                "window_index": position,
                "token_start": start,
                "token_end": end,
            },
        })
        position += 1
        if end >= len(tokens):
            break
        start += stride
    return chunks