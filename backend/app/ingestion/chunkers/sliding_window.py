from __future__ import annotations

import re
from typing import Any, Dict, List


def sliding_window_chunker(text: str, window_size: int = 25, stride: int = 10, document_id: str = "doc-1", language: str = "en") -> List[Dict[str, Any]]:
    """Split text using sliding window with overlap for context preservation."""
    if not text or not text.strip():
        return []
    
    tokens = re.findall(r"\S+", text)
    if not tokens:
        return []

    chunks: List[Dict[str, Any]] = []
    position = 0
    
    for start in range(0, len(tokens), stride):
        end = min(start + window_size, len(tokens))
        snippet = " ".join(tokens[start:end])
        
        if not snippet.strip():
            continue
        
        token_count = len(snippet.split())
        # Rough char count for metadata
        char_count = len(snippet)
        
        chunks.append({
            "chunk_id": f"{document_id}-window-{position}",
            "document_id": document_id,
            "chunk_strategy": "sliding_window",
            "position": position,
            "token_count": max(1, token_count),
            "language": language,
            "text": snippet,
            "metadata": {
                "window_index": position,
                "token_start": start,
                "token_end": end,
                "char_count": char_count,
                "stride": stride,
            },
        })
        position += 1
        
        if end == len(tokens):
            break
    
    return chunks
