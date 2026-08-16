"""Runtime index store: loads offline artifacts and serves search.

Loads the FAISS dense index + chunk metadata + BM25 once, keeps them in
memory, and exposes strategy-filtered search. Built offline by
``backend.app.ingestion.embed_and_index`` — never at query time.
"""

from __future__ import annotations

import json
import threading
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np

from backend.app.config import (
    BM25_TOP_K,
    CHUNKS_PATH,
    DENSE_TOP_K,
    INDEX_PATH,
    RRF_K,
)
from backend.app.retrieval.bm25 import BM25Index, tokenize
from backend.app.retrieval.fusion import reciprocal_rank_fusion

_lock = threading.Lock()
_exists_cache: Dict[str, bool] = {}


def _cached_exists(path: str) -> bool:
    if path not in _exists_cache:
        from pathlib import Path

        _exists_cache[path] = Path(path).exists()
    return _exists_cache[path]


class IndexStore:
    def __init__(self, index_path: str, chunks_path: str):
        self.faiss = faiss.read_index(index_path)
        with open(chunks_path, encoding="utf-8") as f:
            self.chunks = [json.loads(line) for line in f]
        self.n = len(self.chunks)

        self.strategy_positions: Dict[str, np.ndarray] = {}
        for pos, chunk in enumerate(self.chunks):
            strat = chunk.get("chunk_strategy", "sentence")
            self.strategy_positions.setdefault(strat, []).append(pos)
        for strat, positions in self.strategy_positions.items():
            self.strategy_positions[strat] = np.asarray(positions, dtype=np.int64)

        self.bm25 = BM25Index([c["text"] for c in self.chunks])

    # --- dense ----------------------------------------------------------------
    def search_dense(
        self,
        query_vec: np.ndarray,
        top_k: int = DENSE_TOP_K,
        strategy: Optional[str] = None,
    ) -> List[Tuple[int, float]]:
        params = None
        if strategy is not None:
            ids = self.strategy_positions.get(strategy)
            if ids is None or len(ids) == 0:
                return []
            params = faiss.SearchParameters(sel=faiss.IDSelectorBatch(ids.tolist()))
        if query_vec.ndim == 1:
            query_vec = query_vec[None, :]
        scores, indexes = self.faiss.search(query_vec, top_k, params=params)
        results = []
        for score, idx in zip(scores[0], indexes[0]):
            if idx < 0:
                continue
            results.append((int(idx), float(score)))
        return results

    # --- lexical --------------------------------------------------------------
    def search_bm25(
        self,
        query: str,
        top_k: int = BM25_TOP_K,
        strategy: Optional[str] = None,
    ) -> List[Tuple[int, float]]:
        hits = self.bm25.search(query, top_k=top_k * 3)
        if strategy is not None:
            positions = self.strategy_positions.get(strategy)
            if positions is None:
                positions = np.arange(self.n, dtype=np.int64)
            allowed = set(positions.tolist())
            hits = [(i, s) for i, s in hits if i in allowed]
        return hits[:top_k]

    def chunk_text(self, position: int) -> str:
        return self.chunks[position]["text"]

    def chunk_meta(self, position: int) -> dict:
        meta = dict(self.chunks[position])
        meta["score"] = 0.0
        return meta


def available() -> bool:
    return _cached_exists(INDEX_PATH) and _cached_exists(CHUNKS_PATH)


def load(index_path: Optional[str] = None, chunks_path: Optional[str] = None) -> Optional[IndexStore]:
    index_path = index_path or str(INDEX_PATH)
    chunks_path = chunks_path or str(CHUNKS_PATH)
    if not _cached_exists(index_path) or not _cached_exists(chunks_path):
        return None
    return IndexStore(index_path, chunks_path)


def hybrid_retrieve(
    store: IndexStore,
    query_vec: np.ndarray,
    query_text: str,
    top_k: int = 8,
    strategy: Optional[str] = None,
) -> List[Tuple[int, float]]:
    """Dense + BM25 with Reciprocal Rank Fusion (optionally strategy-filtered)."""
    dense_hits = store.search_dense(query_vec, top_k=DENSE_TOP_K, strategy=strategy)
    bm25_hits = store.search_bm25(query_text, top_k=BM25_TOP_K, strategy=strategy)
    fused = reciprocal_rank_fusion(dense_hits, bm25_hits, k=RRF_K)
    return fused[:top_k]