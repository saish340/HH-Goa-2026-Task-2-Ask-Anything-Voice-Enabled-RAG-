from __future__ import annotations

import re
from typing import Any, Dict, List


def sentence_chunker(text: str, document_id: str = "doc-1", language: str = "en") -> List[Dict[str, Any]]:
    """Split text into sentence-level chunks with metadata."""
    if not text or not text.strip():
        return []
    
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: List[Dict[str, Any]] = []
    
    for idx, part in enumerate(parts, start=1):
        cleaned = part.strip()
        if not cleaned:
            continue
        
        # Token count: ~1 word ≈ 1.3 tokens
        word_count = len(cleaned.split())
        token_count = max(1, int(word_count * 1.3))
        
        chunks.append({
            "chunk_id": f"{document_id}-sentence-{idx}",
            "document_id": document_id,
            "chunk_strategy": "sentence",
            "position": idx,
            "token_count": token_count,
            "language": language,
            "text": cleaned,
            "metadata": {"sentence_index": idx, "char_count": len(cleaned)},
        })
    return chunks

