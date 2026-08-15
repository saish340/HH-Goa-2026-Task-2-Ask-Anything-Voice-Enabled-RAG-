from __future__ import annotations

from typing import Any, Dict, List


def build_metadata(document_id: str, strategy: str, position: int, text: str, language: str = "en") -> Dict[str, Any]:
    return {
        "chunk_id": f"{document_id}-{strategy}-{position}",
        "document_id": document_id,
        "chunk_strategy": strategy,
        "position": position,
        "token_count": len(text.split()),
        "language": language,
        "text": text,
    }


def chunk_records_from_texts(document_id: str, texts: List[str], strategy: str, language: str = "en") -> List[Dict[str, Any]]:
    return [
        build_metadata(document_id, strategy, idx + 1, text, language)
        for idx, text in enumerate(texts)
        if text and text.strip()
    ]
