from __future__ import annotations

import math
import re
from typing import List, Sequence, Tuple


def tokenize(text: str) -> List[str]:
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


class BM25Index:
    def __init__(self, corpus: Sequence[str]):
        self.corpus = [text for text in corpus if text]
        self.doc_freq = {}
        self.doc_len = []
        self.avgdl = 0.0
        self.idf = []
        self.tokenized_docs = [tokenize(text) for text in self.corpus]

        doc_count = len(self.tokenized_docs)
        for tokens in self.tokenized_docs:
            self.doc_len.append(len(tokens))
            uniq = set(tokens)
            for token in uniq:
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1
        self.avgdl = sum(self.doc_len) / max(1, doc_count)

        for token, df in self.doc_freq.items():
            self.idf.append((token, math.log((doc_count - df + 0.5) / (df + 0.5) + 1.0)))
        self.idf_dict = dict(self.idf)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        q_tokens = tokenize(query)
        if not q_tokens or not self.corpus:
            return []
        scores: List[Tuple[int, float]] = []
        for idx, doc_tokens in enumerate(self.tokenized_docs):
            score = 0.0
            doc_len = self.doc_len[idx]
            for token in set(q_tokens):
                if token not in self.idf_dict:
                    continue
                term_freq = doc_tokens.count(token)
                numerator = self.idf_dict[token] * term_freq * (1.5 + 1.0)
                denominator = term_freq + 1.5 * (1.0 - 0.75 + 0.75 * (doc_len / self.avgdl if self.avgdl else 1.0))
                if denominator > 0:
                    score += numerator / denominator
            scores.append((idx, score))
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
