"""Quality benchmark: retrieval quality + guardrail behavior.

Part A — retrieval quality (Recall@5/@10, MRR) over labeled MSMARCO-XI queries.
Part B — behavior (grounded rate, correct refusal rate, error rate) across the
categorized test set (normal/paraphrase/noisy/multilingual/off-topic/
unanswerable/adversarial).
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from backend.app.config import BENCH_DIR, TEST_QUERIES_PATH
from backend.app.harness.orchestrator import run_query, warmup
from backend.app.ingestion.ingest import load_eval_queries
from backend.app.retrieval.embeddings import embed_query
from backend.app.retrieval.strategy import route_strategy
from backend.app.retrieval.store import load

REPORT_DIR = BENCH_DIR / "reports"
RETRIEVAL_N = 150


def retrieval_metrics(store, n: int = RETRIEVAL_N) -> dict:
    labeled = [q for q in load_eval_queries() if q["selected_passage_ids"]]
    labeled = labeled[:n]
    if not labeled:
        return {"available": False}

    recalls5, recalls10, mrrs = [], [], []
    for q in labeled:
        strat = route_strategy(q["query"])
        strat_filter = None if strat == "all" else strat
        query_text = q["query"]

        def is_rel(chunk) -> bool:
            try:
                return int(chunk.get("document_id")) in selected
            except (TypeError, ValueError):
                return False

        order = _faithful_order(store, query_text, strat_filter)
        metas = [store.chunk_meta(pos) for pos in order]
        selected = set(q["selected_passage_ids"])

        recalls5.append(1.0 if any(is_rel(m) for m in metas[:5]) else 0.0)
        recalls10.append(1.0 if any(is_rel(m) for m in metas[:10]) else 0.0)

        mrr = 0.0
        for rank, meta in enumerate(metas, start=1):
            if is_rel(meta):
                mrr = 1.0 / rank
                break
        mrrs.append(mrr)

    return {
        "available": True,
        "test_queries": len(labeled),
        "recall_at_5_pct": round(100 * statistics.mean(recalls5), 2),
        "recall_at_10_pct": round(100 * statistics.mean(recalls10), 2),
        "mrr": round(statistics.mean(mrrs), 3),
    }


def _faithful_order(store, query_text: str, strat_filter) -> list:
    """Order of chunks the live pipeline would present (dense+BM25 RRF, then
    cross-encoder rerank over up to RERANK_MAX_CHUNKS candidates)."""
    from backend.app.config import (
        BM25_TOP_K,
        DENSE_TOP_K,
        RERANK_MAX_CHUNKS,
        RERANK_TOP_K,
    )
    from backend.app.harness.orchestrator import rerank_passages
    from backend.app.harness.query_processor import detect_language
    from backend.app.retrieval.fusion import reciprocal_rank_fusion

    dense_hits = store.search_dense(embed_query(query_text), top_k=DENSE_TOP_K, strategy=strat_filter)
    bm25_hits = store.search_bm25(query_text, top_k=BM25_TOP_K, strategy=strat_filter)
    fused_all = reciprocal_rank_fusion(dense_hits, bm25_hits)[:RERANK_MAX_CHUNKS]

    if detect_language(query_text) != "en" or not fused_all:
        return [pos for pos, _ in fused_all[:10]]

    candidates = [(pos, store.chunk_text(pos)) for pos, _ in fused_all]
    reranked = rerank_passages(query_text, candidates, RERANK_TOP_K)
    return [pos for pos, _ in reranked[:10]]


def behavior_metrics() -> dict:
    data = json.loads(Path(TEST_QUERIES_PATH).read_text(encoding="utf-8"))
    categories = [k for k in data if k != "_meta"]

    per_category: dict[str, dict] = {}
    correct_total, answer_total, refuse_total = 0, 0, 0
    answer_hits, refuse_hits = 0, 0
    errors = 0
    total = 0

    for cat in categories:
        entries = data[cat]
        ok = 0
        for entry in entries:
            total += 1
            try:
                res = run_query(entry["query"], tier="fast")
            except Exception:
                errors += 1
                continue
            status = res.get("status")
            expects = entry["expects_answer"]
            if expects:
                answer_total += 1
                correct = status == "ok" and res.get("grounded") is True
                if status == "ok" and res.get("grounded"):
                    answer_hits += 1
            else:
                refuse_total += 1
                correct = status == "refused"
                if status == "refused":
                    refuse_hits += 1
            ok += 1 if correct else 0
        per_category[cat] = {
            "n": len(entries),
            "accuracy_pct": round(100 * ok / max(1, len(entries)), 2),
        }
        correct_total += ok

    grounded_rate = 100 * answer_hits / max(1, answer_total)
    refusal_rate = 100 * refuse_hits / max(1, refuse_total)
    return {
        "test_queries": total,
        "overall_accuracy_pct": round(100 * correct_total / max(1, total), 2),
        "grounded_answer_rate_pct": round(grounded_rate, 2),
        "correct_refusal_rate_pct": round(refusal_rate, 2),
        "error_rate_pct": round(100 * errors / max(1, total), 2),
        "per_category": per_category,
    }


def run() -> dict:
    warmup()
    store = load()

    print("Retrieval metrics ...")
    retrieval = retrieval_metrics(store) if store else {"available": False}
    print("  ", retrieval)

    print("Behavior metrics ...")
    behavior = behavior_metrics()
    print("  ", behavior)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = {"retrieval": retrieval, "behavior": behavior, "dataset": "MSMARCO-XI"}
    (REPORT_DIR / "quality.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (REPORT_DIR / "quality.md").write_text(markdown(out), encoding="utf-8")
    print("Reports written to", REPORT_DIR)
    return out


def markdown(out: dict) -> str:
    r, b = out["retrieval"], out["behavior"]
    lines = [
        "# Quality report",
        "",
        f"Dataset: MSMARCO-XI",
    ]
    if r.get("available"):
        lines += [
            "",
            "## Retrieval",
            f"Test queries: {r['test_queries']}",
            f"Recall@5: {r['recall_at_5_pct']}%",
            f"Recall@10: {r['recall_at_10_pct']}%",
            f"MRR: {r['mrr']}",
        ]
    lines += [
        "",
        "## Guardrails / behavior",
        f"Test queries: {b['test_queries']}",
        f"Overall accuracy: {b['overall_accuracy_pct']}%",
        f"Grounded answers: {b['grounded_answer_rate_pct']}%",
        f"Correct refusals: {b['correct_refusal_rate_pct']}%",
        f"Error rate: {b['error_rate_pct']}%",
        "",
        "| Category | n | Accuracy |",
        "|---|---|---|",
    ]
    for cat, stats in b["per_category"].items():
        lines.append(f"| {cat} | {stats['n']} | {stats['accuracy_pct']}% |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())