"""Dense retrieval over the offline FAISS index."""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import numpy as np

from backend.app.retrieval.embeddings import embed_query
from backend.app.retrieval.store import IndexStore


class DenseIndex:
    def __init__(self, store: Optional[IndexStore] = None):
        self.store = store

    def search(
        self,
        query: str,
        top_k: int = 20,
        strategy: Optional[str] = None,
    ) -> List[Tuple[int, float]]:
        if self.store is None:
            return []
        query_vec = embed_query(query)
        return self.store.search_dense(query_vec, top_k=top_k, strategy=strategy)

    @staticmethod
    def vectorize(texts: Sequence[str]) -> np.ndarray:
        from backend.app.retrieval.embeddings import embed_texts

        return embed_texts(list(texts))