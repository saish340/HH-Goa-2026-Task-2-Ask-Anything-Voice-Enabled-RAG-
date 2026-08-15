from fastapi.testclient import TestClient

from backend.app.harness.orchestrator import run_query
from backend.app.ingestion.chunkers.sentence import sentence_chunker
from backend.app.main import app
from backend.app.retrieval.hybrid import HybridRetriever


def test_run_query_returns_grounded_response():
    result = run_query("What is the capital of France?")
    assert result["query"] == "What is the capital of France?"
    assert result["grounded"] is True
    assert len(result["retrieved_chunks"]) >= 1
    assert result["confidence"] >= 0.0


def test_run_query_rejects_off_topic():
    result = run_query("How to bake a cake in the moon?")
    assert result["grounded"] is False or result["answer"] == "I can only answer questions about the local knowledge base."


def test_api_post_ask_returns_json_response():
    client = TestClient(app)
    response = client.post("/api/ask", json={"query": "What is the capital of France?"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "What is the capital of France?"
    assert "Paris" in body["answer"]


def test_api_benchmark_endpoint_returns_metrics():
    client = TestClient(app)
    response = client.get("/api/benchmarks")
    assert response.status_code == 200
    body = response.json()
    assert "p50" in body
    assert "recall_at_5" in body


def test_sentence_chunker_returns_multiple_metadata_chunks():
    text = "Paris is the capital of France. India has New Delhi as its capital. Science studies nature."
    chunks = sentence_chunker(text, document_id="doc-1")
    assert len(chunks) >= 2
    first = chunks[0]
    assert first["document_id"] == "doc-1"
    assert first["chunk_strategy"] == "sentence"
    assert first["token_count"] > 0


def test_hybrid_retriever_returns_ranked_results():
    docs = [
        "Paris is the capital city of France.",
        "India has New Delhi as its capital.",
        "Science studies the natural world.",
    ]
    retriever = HybridRetriever(docs)
    hits = retriever.retrieve("What is the capital of France?")
    assert len(hits) >= 1
    assert hits[0]["text"].lower().startswith("paris")
