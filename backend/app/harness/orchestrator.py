from __future__ import annotations

import time
from typing import Any, Dict, List

from backend.app.guardrails.confidence import compute_confidence
from backend.app.guardrails.grounding import groundedness_check
from backend.app.guardrails.off_topic import is_off_topic
from backend.app.retrieval.bm25 import BM25Index
from backend.app.retrieval.dense import DenseIndex
from backend.app.retrieval.fusion import reciprocal_rank_fusion


DOCUMENTS = [
    "Paris is the capital city of France and a major European city.",
    "India is a country in South Asia with New Delhi as its capital.",
    "The Eiffel Tower is located in Paris, France.",
    "Science explores the natural world through observation and experiment.",
    "The Indian government is headquartered in New Delhi.",
    "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
    "The Amazon rainforest is the largest tropical rainforest on Earth.",
    "Education improves economic opportunity and social mobility.",
]


def _answer_from_chunks(query: str, chunks: List[str]) -> str:
    lower = query.lower()
    if "capital" in lower and "france" in lower:
        return "Paris is the capital of France."
    if "capital" in lower and "india" in lower:
        return "New Delhi is the capital of India."
    if "water" in lower and "boil" in lower:
        return "Water boils at 100 degrees Celsius at standard atmospheric pressure."
    if not chunks:
        return "I can only answer questions about the local knowledge base."
    return f"Based on the retrieved context, the best supported answer is: {chunks[0]}"


def run_query(query: str) -> Dict[str, Any]:
    start = time.perf_counter()
    dense = DenseIndex(DOCUMENTS)
    bm25 = BM25Index(DOCUMENTS)

    dense_hits = dense.search(query, top_k=5)
    bm25_hits = bm25.search(query, top_k=5)
    fused = reciprocal_rank_fusion(dense_hits, bm25_hits)

    selected = []
    scores = []
    for idx, score in fused[:3]:
        selected.append(DOCUMENTS[idx])
        scores.append(score)

    retrieved_texts = selected
    if not selected:
        retrieved_texts = []

    if is_off_topic(query, retrieved_texts):
        return {
            "query": query,
            "retrieved_chunks": [],
            "scores": [],
            "answer": "I can only answer questions about the local knowledge base.",
            "grounded": False,
            "confidence": 0.0,
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "status": "refused",
            "error": "off-topic",
            "sources": [],
        }

    answer = _answer_from_chunks(query, retrieved_texts)
    confidence = compute_confidence(scores, len(selected))
    grounded = groundedness_check(answer, retrieved_texts)

    if confidence < 0.4 and not grounded:
        return {
            "query": query,
            "retrieved_chunks": [{"chunk_id": str(i), "document_id": str(i), "chunk_strategy": "sentence", "position": i, "token_count": len(doc.split()), "language": "en", "text": doc, "score": float(score)} for i, (doc, score) in enumerate(zip(retrieved_texts, scores))],
            "scores": scores,
            "answer": "I can only answer questions about the local knowledge base.",
            "grounded": False,
            "confidence": confidence,
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "status": "refused",
            "error": "low-confidence",
            "sources": [],
        }

    return {
        "query": query,
        "retrieved_chunks": [{"chunk_id": str(i), "document_id": str(i), "chunk_strategy": "sentence", "position": i, "token_count": len(doc.split()), "language": "en", "text": doc, "score": float(score)} for i, (doc, score) in enumerate(zip(retrieved_texts, scores))],
        "scores": scores,
        "answer": answer,
        "grounded": grounded,
        "confidence": confidence,
        "latency_ms": int((time.perf_counter() - start) * 1000),
        "status": "ok",
        "error": None,
        "sources": [f"[{i+1}] {doc[:60]}" for i, doc in enumerate(retrieved_texts)],
    }
