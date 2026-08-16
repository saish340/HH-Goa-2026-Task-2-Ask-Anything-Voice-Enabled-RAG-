"""Shared sentence-embedding accessor (lazy singleton)."""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from backend.app.config import DEVICE, EMBEDDING_MODEL

_encoder = None


def get_encoder():
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer

        _encoder = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)
    return _encoder


def embed_texts(texts: List[str], batch_size: int = 128) -> np.ndarray:
    """Embed a list of strings and return an L2-normalized float32 matrix."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    encoder = get_encoder()
    vectors = encoder.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return np.asarray(vectors, dtype=np.float32)


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text], batch_size=1)[0]


def warmup() -> None:
    """Force encoder load so first real request avoids the load stall."""
    global _encoder
    if _encoder is None:
        _encoder = get_encoder()
    _ = embed_query("warmup")