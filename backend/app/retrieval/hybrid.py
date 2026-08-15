from __future__ import annotations

from typing import Any, Dict, List

from backend.app.retrieval.bm25 import BM25Index
from backend.app.retrieval.dense import DenseIndex
from backend.app.retrieval.fusion import reciprocal_rank_fusion


class HybridRetriever:
    def __init__(self, corpus: List[str]):
        self.corpus = corpus
        self.dense = DenseIndex(corpus)
        self.bm25 = BM25Index(corpus)

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        dense_hits = self.dense.search(query, top_k=top_k)
        bm25_hits = self.bm25.search(query, top_k=top_k)
        fused = reciprocal_rank_fusion(dense_hits, bm25_hits)

        results = []
        for idx, score in fused[:top_k]:
            text = self.corpus[idx]
            results.append({
                "document_id": str(idx),
                "chunk_strategy": "hybrid",
                "text": text,
                "score": float(score),
            })
        return results
