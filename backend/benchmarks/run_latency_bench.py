"""Latency benchmark: P50/P70/P100 + per-stage breakdown, honest numbers.

RAG-only (query → answer), two tiers:
- fast tier (extractive answer) over >=100 queries
- llm tier (generative answer) over a smaller sample (mm-scale decode)
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import numpy as np

from backend.app.config import BENCH_DIR
from backend.app.harness.orchestrator import run_query, warmup
from backend.app.ingestion.ingest import load_eval_queries

REPORT_DIR = BENCH_DIR / "reports"
N_FAST = 120
N_LLM = 25

STAGES = [
    "query_processing",
    "embedding",
    "dense",
    "bm25",
    "fusion",
    "rerank",
    "generation",
    "guardrail",
]


def _pick_queries(n: int):
    labeled = [q for q in load_eval_queries() if q["selected_passage_ids"]]
    fillers = [
        "What is the winning lottery number on 1st August 2026?",
        "How do I fix a leaking tap?",
        "What is the price of Bitcoin today?",
        "Which is the best music streaming app?",
        "How do I train my dog to sit?",
        "What should I wear to an interview?",
        "How do I plan a road trip?",
        "Why is my WiFi signal weak?",
        "Explain the meaning of life.",
        "Who is the best goalkeeper in world football?",
    ]
    take_fillers = min(len(fillers), n)
    labeled = [q["query"] for q in labeled]
    queries = labeled[: max(0, n - take_fillers)] + fillers[:take_fillers]
    return queries[:n]


def percentiles(vals: list[float]) -> dict[str, float]:
    s = sorted(vals)
    n = len(s)
    p50 = statistics.median(s)
    p70 = np.percentile(s, 70) if n >= 7 else s[-1]
    p100 = s[-1]
    return {"p50": round(p50, 2), "p70": round(float(p70), 2), "p100": round(float(p100), 2)}


def bench(tier: str, queries: list[str]) -> dict:
    latencies: list[float] = []
    per_stage: dict[str, list[float]] = {s: [] for s in STAGES}
    refused = 0
    errors = 0
    for q in queries:
        try:
            res = run_query(q, tier=tier)
            latencies.append(float(res["latency_ms"]))
            for stage in STAGES:
                per_stage[stage].append(float(res["per_stage_ms"].get(stage, 0.0)))
            if res["status"] == "refused":
                refused += 1
            if res["status"] == "error":
                errors += 1
        except Exception:
            errors += 1
            latencies.append(float("nan"))

    clean = [v for v in latencies if v == v]
    stage_p50 = {s: round(statistics.median([v for v in per_stage[s] if v == v]), 3) for s in STAGES}
    report = {
        "tier": tier,
        "test_queries": len(queries),
        "percentiles_ms": percentiles(clean),
        "mean_ms": round(statistics.mean(clean), 2),
        "stage_p50_ms": stage_p50,
        "refused": refused,
        "errors": errors,
        "note": "STT and out-of-process network latency are reported separately (see README).",
    }
    return report


def run() -> dict:
    warmup()
    fast_queries = _pick_queries(N_FAST)
    llm_queries = _pick_queries(N_LLM)

    print(f"Benchmarking fast tier over {len(fast_queries)} queries ...")
    fast = bench("fast", fast_queries)
    print("  done", fast["percentiles_ms"])

    print(f"Benchmarking llm tier over {len(llm_queries)} queries ...")
    llm = bench("llm", llm_queries)
    print("  done", llm["percentiles_ms"])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = {"fast_tier": fast, "llm_tier": llm, "source": "MSMARCO-XI"}
    (REPORT_DIR / "latency.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (REPORT_DIR / "latency.md").write_text(markdown(out), encoding="utf-8")
    print("Reports written to", REPORT_DIR)
    return out


def markdown(out: dict) -> str:
    lines = ["# Latency report — RAG only (query → answer)", ""]
    for tier, report in out.items():
        if tier not in ("fast_tier", "llm_tier"):
            continue
        p = report["percentiles_ms"]
        lines += [
            f"## {tier} tier",
            "",
            f"Test queries: {report['test_queries']}",
            f"P50: {p['p50']} ms / P70: {p['p70']} ms / P100: {p['p100']} ms",
            "",
            "| Stage | P50 (ms) |",
            "|---|---|",
        ]
        for stage, ms in report["stage_p50_ms"].items():
            lines.append(f"| {stage} | {ms} |")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())