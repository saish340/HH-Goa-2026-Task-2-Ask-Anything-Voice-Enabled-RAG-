"""Central configuration for the Ask Anything pipeline.

All model ids, artifact paths, and guardrail thresholds live here so the
pipeline can be tuned without touching code across modules.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Paths -------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.environ.get("AA_DATA_DIR", REPO_ROOT / "data"))
INDEX_PATH = DATA_DIR / "index.faiss"
CHUNKS_PATH = DATA_DIR / "chunks.jsonl"
PASSAGES_PATH = DATA_DIR / "passages.jsonl"
QUERIES_PATH = DATA_DIR / "eval_queries.jsonl"
BENCH_DIR = REPO_ROOT / "backend" / "benchmarks"
TEST_QUERIES_PATH = BENCH_DIR / "test_queries.json"

# --- Compute ------------------------------------------------------------------
FORCE_CPU = os.environ.get("AA_FORCE_CPU", "0") == "1"
DEVICE = os.environ.get("AA_DEVICE", "cpu" if FORCE_CPU else "cuda")

# --- Models ------------------------------------------------------------------
EMBEDDING_MODEL = os.environ.get(
    "AA_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
RERANK_MODEL = os.environ.get("AA_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
LLM_MODEL = os.environ.get("AA_LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
LLM_MAX_NEW_TOKENS = int(os.environ.get("AA_LLM_MAX_NEW_TOKENS", "32"))
LLM_FALLBACK_MODEL = os.environ.get("AA_LLM_FALLBACK_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")

# --- Retrieval ----------------------------------------------------------------
EMBEDDING_DIM = int(os.environ.get("AA_EMBEDDING_DIM", "384"))
DENSE_TOP_K = int(os.environ.get("AA_DENSE_TOP_K", "20"))
BM25_TOP_K = int(os.environ.get("AA_BM25_TOP_K", "20"))
FUSION_TOP_K = int(os.environ.get("AA_FUSION_TOP_K", "8"))
RRF_K = int(os.environ.get("AA_RRF_K", "60"))
RERANK_TOP_K = int(os.environ.get("AA_RERANK_TOP_K", "8"))
RERANK_MAX_CHUNKS = int(os.environ.get("AA_RERANK_MAX_CHUNKS", "12"))

# --- Guardrails ---------------------------------------------------------------
# Minimal cosine similarity between query and best retrieved chunk before we
# consider the retrieval on-topic.
OFF_TOPIC_COSINE_THRESHOLD = float(os.environ.get("AA_OFF_TOPIC_COSINE", "0.58"))
# Minimal fusion score (0..1 mapped) accepted before refusing.
CONFIDENCE_MIN = float(os.environ.get("AA_CONFIDENCE_MIN", "0.25"))
# Minimal grounding score (0..1) required to label the answer SUPPORTED.
GROUNDING_MIN = float(os.environ.get("AA_GROUNDING_MIN", "0.30"))
# Minimal query↔answer-sentence semantic similarity for the extractive tier to
# consider a response relevant; below this we refuse as ungrounded.
EXTRACT_MIN_SIM = float(os.environ.get("AA_EXTRACT_MIN_SIM", "0.50"))
# Minimal fraction of query significant terms covered by the answer sentence
# (skipped for non-Latin queries, where lexical coverage is meaningless).
EXTRACT_MIN_COVERAGE = float(os.environ.get("AA_EXTRACT_MIN_COVERAGE", "0.25"))
# Answers shorter than this word count are treated as garbage / refused.
EXTRACT_MIN_WORDS = int(os.environ.get("AA_EXTRACT_MIN_WORDS", "3"))
# When the reranker runs, a top passage scoring below this cross-encoder value
# is treated as a failed/unsupported retrieval and refused. On-topic queries
# typically score >6; irrelevant-but-lexically-near passages score <2.
RERANK_REFUSE_BELOW = float(os.environ.get("AA_RERANK_REFUSE_BELOW", "1.5"))
# Below this value the reranker score alone signals junk (absolutely refuse,
# regardless of the extractive score).
RERANK_REFUSE_HARD = float(os.environ.get("AA_RERANK_REFUSE_HARD", "0.5"))
# Extractive relevance above this exempts a passage from the reranker gate
# (the retrieval snippet genuinely responds to the query).
EXTRACT_STRONG = float(os.environ.get("AA_EXTRACT_STRONG", "0.6"))

# --- Strategy routing ---------------------------------------------------------
SHORT_QUERY_WORD_MAX = int(os.environ.get("AA_SHORT_QUERY_WORD_MAX", "12"))


# --- Torch tuning (idempotent, safe when torch is unavailable) ----------------
def _tune_torch() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
    except Exception:
        pass


_tune_torch()