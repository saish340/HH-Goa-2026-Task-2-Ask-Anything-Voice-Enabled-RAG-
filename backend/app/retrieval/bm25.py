"""BM25 lexical retrieval with inverted postings (fast on large corpora).

Implements BM25 (b = 0.75, k1 = 1.5) with a proper inverted index so scoring
only touches documents that share a query token, keeping the lexical stage
cheap enough to fit the latency budget.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Dict, List, Sequence, Tuple


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


STOPWORDS = {
    "the", "and", "of", "to", "a", "in", "on", "for", "is", "are", "was",
    "were", "be", "been", "it", "its", "this", "that", "with", "as", "by",
    "at", "or", "do", "does", "did", "an", "not", "but", "from", "what",
    "which", "how", "why", "who", "when", "where", "i", "you", "your", "me",
}


def query_tokens(query: str) -> List[str]:
    """Query tokens with high-frequency stopwords dropped (they dominate postings)."""
    return [tok for tok in tokenize(query) if tok not in STOPWORDS]


class BM25Index:
    def __init__(self, corpus: Sequence[str]):
        self.corpus = list(corpus)
        self.n_docs = max(1, len(self.corpus))
        self.doc_len: List[int] = []
        self.avgdl = 0.0
        self.postings: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        self.idf: Dict[str, float] = {}
        self._build()

    def _build(self) -> None:
        doc_freq: Dict[str, int] = defaultdict(int)
        total_len = 0
        for doc_idx, text in enumerate(self.corpus):
            token_counts: Dict[str, int] = defaultdict(int)
            for tok in tokenize(text):
                token_counts[tok] += 1
            total_len += sum(token_counts.values())
            self.doc_len.append(sum(token_counts.values()))
            for tok, tf in token_counts.items():
                if not self.postings[tok] or self.postings[tok][-1][0] != doc_idx:
                    doc_freq[tok] += 1
                self.postings[tok].append((doc_idx, tf))

        self.avgdl = total_len / self.n_docs if self.n_docs else 0.0
        for tok, df in doc_freq.items():
            self.idf[tok] = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        q_tokens = query_tokens(query)
        if not q_tokens:
            return []
        k1, b = 1.5, 0.75
        scores: Dict[int, float] = defaultdict(float)
        for tok in set(q_tokens):
            idf = self.idf.get(tok)
            if idf is None:
                continue
            for doc_idx, tf in self.postings.get(tok, []):
                doc_len = self.doc_len[doc_idx]
                denom = tf + k1 * (1.0 - b + b * (doc_len / self.avgdl if self.avgdl else 1.0))
                scores[doc_idx] += idf * (tf * (k1 + 1.0)) / max(denom, 1e-9)

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        return [(doc_idx, float(score)) for doc_idx, score in ranked]