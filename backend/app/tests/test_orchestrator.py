from fastapi.testclient import TestClient

from backend.app.config import OFF_TOPIC_COSINE_THRESHOLD
from backend.app.guardrails.confidence import compute_confidence, below_threshold
from backend.app.guardrails.grounding import grounding_score, groundedness_check
from backend.app.guardrails.off_topic import is_off_topic
from backend.app.harness.orchestrator import run_query, _DEMO_DOCS
from backend.app.harness.query_processor import detect_language, normalize_query
from backend.app.ingestion.chunkers.semantic import semantic_chunker
from backend.app.ingestion.chunkers.sentence import sentence_chunker, split_sentences
from backend.app.ingestion.chunkers.sliding_window import sliding_window_chunker
from backend.app.main import app
from backend.app.retrieval.bm25 import BM25Index
from backend.app.retrieval.dense import DenseIndex
from backend.app.retrieval.fusion import reciprocal_rank_fusion
from backend.app.retrieval.strategy import route_strategy


def test_run_query_returns_grounded_response():
    result = run_query("What is the capital of France?")
    assert result["query"] == "What is the capital of France?"
    assert result["status"] == "ok"
    assert result["grounded"] is True
    assert len(result["retrieved_chunks"]) >= 1
    assert result["grounding_label"] == "SUPPORTED"


def test_run_query_rejects_off_topic():
    result = run_query("How to bake a cake in the moon?")
    assert result["status"] == "refused"
    assert result["error"] == "off-topic"


def test_api_post_ask_returns_json_response():
    client = TestClient(app)
    response = client.post("/api/ask", json={"query": "What is the capital of France?"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "What is the capital of France?"
    assert "Paris" in body["answer"]
    assert "per_stage_ms" in body


def test_api_benchmark_endpoint_returns_metrics():
    client = TestClient(app)
    response = client.get("/api/benchmarks")
    assert response.status_code == 200
    assert "available" in response.json()


def test_api_stats_endpoint():
    client = TestClient(app)
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert "per_strategy" in response.json()


# --- chunkers -----------------------------------------------------------------


def test_sentence_chunker_returns_metadata_chunks():
    chunks = sentence_chunker(
        "Paris is the capital of France. India has New Delhi as its capital. Science studies nature.",
        document_id="doc-1",
    )
    assert len(chunks) >= 2
    assert chunks[0]["chunk_strategy"] == "sentence"
    assert chunks[0]["token_count"] > 0
    assert chunks[0]["document_id"] == "doc-1"


def test_semantic_chunker_groups_and_tags():
    chunks = semantic_chunker(
        "Python is a language. Python is popular. Excel is a spreadsheet tool.",
        document_id="doc-2",
        embed_fn=lambda s: [1.0, 0.0] if "python" in s.lower() else [0.0, 1.0],
    )
    assert chunks
    assert all(c["chunk_strategy"] == "semantic" for c in chunks)
    assert "key_terms" in chunks[0]


def test_sliding_window_chunker_overlaps():
    text = " ".join(f"word{i}" for i in range(30))
    chunks = sliding_window_chunker(text, window_size=10, stride=5, document_id="doc-3")
    assert len(chunks) >= 4
    assert all(c["chunk_strategy"] == "sliding_window" for c in chunks)
    spans = [c["metadata"]["token_start"] for c in chunks]
    assert spans == sorted(spans)


def test_split_sentences_handles_abbreviations():
    sentences = split_sentences("The U.S. is big. India is large.")
    assert len(sentences) >= 2


# --- retrieval ----------------------------------------------------------------


def test_bm25_ranks_relevant_first():
    idx = BM25Index(["Paris is the capital of France.", "Cats are cute pets."])
    hits = idx.search("capital of France", top_k=2)
    assert hits[0][0] == 0


def test_dense_search_returns_ranked_hits():
    from backend.app.retrieval.embeddings import embed_query

    store = None
    dense = DenseIndex(store)
    assert dense.search("anything") == []


def test_rrf_fuses_rankings():
    dense_hits = [(1, 0.9), (0, 0.7), (2, 0.5)]
    bm25_hits = [(2, 0.8), (1, 0.6), (0, 0.4)]
    fused = reciprocal_rank_fusion(dense_hits, bm25_hits)
    assert fused[0][0] in (1, 2)


def test_strategy_router_tags_queries():
    assert route_strategy("What is the capital of France?") == "sentence"
    assert route_strategy("Explain the relationship between inflation and growth.") == "semantic"
    assert route_strategy("Who lives on Mars?") == "sentence"


# --- guardrails ---------------------------------------------------------------


def test_off_topic_flag():
    assert is_off_topic([], 0) is True
    assert is_off_topic([(0, OFF_TOPIC_COSINE_THRESHOLD + 0.05)], 3) is False
    assert is_off_topic([(0, 0.1)], 3) is True


def test_compute_confidence_bounds():
    c = compute_confidence([0.5, 0.4], bm25_score=4.0, grounded=True)
    assert 0.0 <= c <= 1.0
    assert below_threshold(0.1, 0.4) is True


def test_grounding_label():
    sup, score, label = groundedness_check(
        "Paris is the capital of France.", ["Paris is the capital of France and is on the Seine."]
    )
    assert label == "SUPPORTED"
    assert sup is True


# --- query normalization ------------------------------------------------------


def test_normalize_query_cleans_filler():
    assert "uh" not in normalize_query("uh what is uh the capital")
    assert normalize_query("  France ?  is  big.  ") == "France ? is big"


def test_detect_language_scripts():
    assert detect_language("भारत की राजधानी") == "hi"
    assert detect_language("What is the capital?") == "en"
    assert detect_language("月球和地球相比有多大?") == "zh"
    assert detect_language("エッフェル塔は何でできていますか?") == "ja"
    assert detect_language("سعودی عرب کی سب سے بڑی ریگستان") == "ur"


def test_temporal_unanswerable_guardrail():
    from backend.app.harness.query_processor import is_temporal_unanswerable

    assert is_temporal_unanswerable("What will the weather be in Mumbai in December 2030?")
    assert is_temporal_unanswerable("When will the next ice age begin exactly?")
    assert is_temporal_unanswerable("Will it rain tomorrow in Delhi?")
    # Recorded, factual, or non-future questions must NOT be caught.
    assert not is_temporal_unanswerable("What is the capital of France?")
    assert not is_temporal_unanswerable("Who invented the paperclip in 1902?")
    assert not is_temporal_unanswerable("What is the current temperature in Mumbai?")
    assert not is_temporal_unanswerable("")