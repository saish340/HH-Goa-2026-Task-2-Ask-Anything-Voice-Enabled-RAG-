"""Hybrid retrieval: dense + BM25 fused with Reciprocal Rank Fusion.

Built on the offline ``IndexStore`` so it never blocks on network I/O.
"""

from __future__ import annotations

from typing import List, Optional

from backend.app.retrieval.bm25 import BM25Index
from backend.app.retrieval.dense import DenseIndex
from backend.app.retrieval.embeddings import embed_query
from backend.app.retrieval.store import IndexStore, hybrid_retrieve


class HybridRetriever:
    def __init__(self, store: Optional[IndexStore] = None, corpus: Optional[List[str]] = None):
        if store is None and corpus:
            store = IndexStore.from_corpus(corpus) if hasattr(IndexStore, "from_corpus") else None
        self.store = store
        self.dense = DenseIndex(store)
        self.bm25 = BM25Index(corpus or [])

    def retrieve(
        self,
        query: str,
        top_k: int = 8,
        strategy: Optional[str] = None,
    ) -> List[dict]:
        if self.store is None:
            return []
        hits = hybrid_retrieve(self.store, embed_query(query), query, top_k=top_k, strategy=strategy)
        return [
            {
                "position": pos,
                "chunk_id": self.store.chunks[pos]["chunk_id"],
                "document_id": self.store.chunks[pos]["document_id"],
                "chunk_strategy": self.store.chunks[pos]["chunk_strategy"],
                "text": self.store.chunk_text(pos),
                "score": float(score),
            }
            for pos, score in hits
        ]