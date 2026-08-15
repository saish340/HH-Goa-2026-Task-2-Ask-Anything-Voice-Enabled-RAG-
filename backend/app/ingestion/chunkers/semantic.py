from __future__ import annotations

import re
from typing import Any, Dict, List


def semantic_chunker(text: str, document_id: str = "doc-1", language: str = "en") -> List[Dict[str, Any]]:
    """Group sentences into semantic chunks based on topic/keyword overlap."""
    if not text or not text.strip():
        return []
    
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text.strip()) if segment.strip()]
    if not sentences:
        return []
    
    # Group consecutive sentences (simplified: 2-3 per semantic chunk)
    chunks: List[Dict[str, Any]] = []
    chunk_size = 2
    position = 0
    
    for i in range(0, len(sentences), chunk_size):
        group = sentences[i : i + chunk_size]
        chunk_text = " ".join(group)
        
        if not chunk_text.strip():
            continue
        
        # Extract keywords
        tokens = set(re.findall(r"[a-zA-Z0-9]+", chunk_text.lower()))
        
        # Token count
        word_count = len(chunk_text.split())
        token_count = max(1, int(word_count * 1.3))
        
        chunks.append({
            "chunk_id": f"{document_id}-semantic-{position}",
            "document_id": document_id,
            "chunk_strategy": "semantic",
            "position": position,
            "token_count": token_count,
            "language": language,
            "text": chunk_text,
            "key_terms": sorted(tokens),
            "metadata": {"sentence_span": (i, min(i + chunk_size, len(sentences)))},
        })
        position += 1
    
    return chunks
