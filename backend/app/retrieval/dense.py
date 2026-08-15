from __future__ import annotations

import re
from typing import List, Sequence, Tuple


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class DenseIndex:
    def __init__(self, corpus: Sequence[str]):
        self.corpus = list(corpus)
        self.term_set = sorted({token for doc in self.corpus for token in normalize_text(doc).split()})

    def _tfidf_vector(self, text: str) -> List[float]:
        tokens = normalize_text(text).split()
        token_count = len(tokens)
        if token_count == 0:
            return [0.0] * len(self.term_set)
        vector = []
        for term in self.term_set:
            freq = tokens.count(term)
            tf = freq / token_count
            df = sum(1 for doc in self.corpus if term in normalize_text(doc).split())
            idf = 1.0 if df == 0 else 1.0 + (len(self.corpus) / df)
            vector.append(tf * idf)
        return vector

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        if not query or not self.corpus:
            return []
        q_vec = self._tfidf_vector(query)
        scores: List[Tuple[int, float]] = []
        for idx, doc in enumerate(self.corpus):
            d_vec = self._tfidf_vector(doc)
            dot = sum(a * b for a, b in zip(q_vec, d_vec))
            norm_q = (sum(v * v for v in q_vec)) ** 0.5
            norm_d = (sum(v * v for v in d_vec)) ** 0.5
            cosine = 0.0 if norm_q == 0 or norm_d == 0 else dot / (norm_q * norm_d)
            scores.append((idx, cosine))
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
