"""Fast extractive answer generation (default tier).

For short, factual queries a deterministic span-extraction from the top
retrieved chunks is dramatically faster than autoregressive decoding while
remaining grounded by construction. The LLM tier in ``llm_client`` handles
complex/conceptual questions.

Scoring: embedding cosine between the query and each candidate sentence,
blended with a lexical-overlap bonus (query-significant tokens covered).
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Sequence

STOPWORDS = {
    "a", "an", "the", "of", "to", "and", "is", "are", "was", "were", "in", "on",
    "at", "it", "its", "for", "with", "that", "this", "or", "as", "by", "from",
    "be", "be", "do", "does", "did", "have", "has", "had", "not", "no", "what",
    "which", "how", "why", "who", "when", "where", "i", "you", "your", "me", "he",
    "she", "they", "we", "us", "of", "the", "a", "an", "will", "would", "can",
}


def _significant(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9']+", text.lower()) if t not in STOPWORDS and len(t) > 1]


def _extract_sentences(contexts: Sequence[str], max_chunks: int = 6) -> List[str]:
    sentences: List[str] = []
    for text in contexts[:max_chunks]:
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent = sent.strip()
            if len(sent) > 12:
                sentences.append(sent)
    return sentences[:32]


def extract_answer(query: str, contexts: Sequence[str], top_k: int = 6) -> Dict[str, Any]:
    t0 = time.perf_counter()
    query_terms = set(_significant(query))
    sentences = _extract_sentences(contexts, top_k)
    # Non-Latin queries (Hindi, Chinese, ...) have no ASCII significant terms;
    # selection then relies purely on embedding similarity.
    if not sentences:
        return {"answer": "", "method": "extractive", "score": 0.0, "ms": int((time.perf_counter() - t0) * 1000)}

    try:
        from backend.app.retrieval.embeddings import embed_texts

        vecs = embed_texts([query] + sentences, batch_size=64)
        q_vec, sent_vecs = vecs[0], vecs[1:]
    except Exception:
        q_vec, sent_vecs = None, [None] * len(sentences)

    best_sentence, best_score, best_coverage = "", -1.0, 0.0
    for i, sent in enumerate(sentences):
        vocab = set(_significant(sent))
        covered = (query_terms & vocab)
        lexical = len(covered) / len(query_terms) if query_terms else 0.0
        semantic = 0.0
        if q_vec is not None and sent_vecs[i] is not None:
            semantic = float(q_vec @ sent_vecs[i])
        length_penalty = 1.0
        n_words = len(sent.split())
        if n_words > 45:
            length_penalty = 0.75
        score = semantic
        if query_terms:
            score = 0.75 * semantic + 0.25 * lexical
        score *= length_penalty
        if score > best_score:
            best_score, best_sentence, best_coverage = score, sent, lexical

    return {
        "answer": best_sentence,
        "method": "extractive",
        "score": round(max(best_score, 0.0), 3),
        "coverage": round(best_coverage, 3),
        "ms": int((time.perf_counter() - t0) * 1000),
    }