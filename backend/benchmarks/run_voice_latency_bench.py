"""End-to-end voice latency benchmark: voice -> STT -> RAG -> answer.

Separate from the RAG-only benchmark because STT is an out-of-process network
call (Sarvam API) whose latency you cannot control.

Requires:
- SARVAM_API_KEY set (Sarvam STT)
- audio samples under data/voice_samples/*.{wav,mp3,m4a,ogg} (default) or the
  dir set via AA_VOICE_SAMPLES_DIR. Record one short question per file; the
  transcribed text is sent to the fast RAG tier.

When either precondition is missing this writes an honest "not measured"
report instead of fabricating numbers.
"""
from __future__ import annotations

import asyncio
import json
import os
import statistics
import time
from pathlib import Path

from backend.app.config import BENCH_DIR, DATA_DIR
from backend.app.harness.orchestrator import run_query, warmup
from backend.benchmarks.run_latency_bench import percentiles

REPORT_DIR = BENCH_DIR / "reports"
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}


def _samples() -> list[Path]:
    default = Path(os.environ.get("AA_VOICE_SAMPLES_DIR", DATA_DIR / "voice_samples"))
    if not default.exists():
        return []
    return sorted(p for p in default.iterdir() if p.suffix.lower() in AUDIO_EXTS)


def _measured() -> dict:
    from backend.app.stt.sarvam_client import transcribe_audio

    samples = _samples()
    stt_ms, rag_ms, e2e_ms, failed, refused, errors = [], [], [], 0, 0, 0

    for sample in samples:
        try:
            t0 = time.perf_counter()
            result = asyncio.run(transcribe_audio(sample.read_bytes(), "en-IN"))
            stt = (time.perf_counter() - t0) * 1000
            transcript = result.get("transcript", "")
            if not transcript:
                failed += 1
                continue
            res = run_query(transcript, tier="fast")
            rag = float(res["latency_ms"])
            if res["status"] == "error":
                errors += 1
            if res["status"] == "refused":
                refused += 1
            stt_ms.append(stt)
            rag_ms.append(rag)
            e2e_ms.append(stt + rag)
        except Exception:
            failed += 1

    return {
        "samples": len(samples),
        "completed": len(e2e_ms),
        "failed_transcripts": failed,
        "refused": refused,
        "errors": errors,
        "rag_only_ms": percentiles(rag_ms),
        "stt_ms": percentiles(stt_ms),
        "end_to_end_ms": percentiles(e2e_ms),
        "note": "STT is a Sarvam network call; end-to-end includes both STT and RAG.",
    }


def run() -> dict:
    key = os.environ.get("SARVAM_API_KEY", "")
    samples = _samples()
    if not key or not samples:
        missing = [x for x, ok in (("SARVAM_API_KEY", bool(key)), ("audio samples", bool(samples))) if not ok]
        out = {
            "available": False,
            "missing": missing,
            "note": "Voice E2E latency not measured locally: set SARVAM_API_KEY and add "
            "audio samples to data/voice_samples/, then re-run.",
        }
    else:
        warmup()
        measured = _measured()
        out = {"available": True, **measured}

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "voice_latency.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (REPORT_DIR / "voice_latency.md").write_text(markdown(out), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return out


def markdown(out: dict) -> str:
    if not out.get("available"):
        return "# Voice end-to-end latency\n\n" f"Status: not measured.\n\n{out.get('note', '')}"
    lines = ["# Voice end-to-end latency (voice -> STT -> RAG -> answer)", ""]
    lines.append(f"Samples: {out['samples']}  completed: {out['completed']}  "
                 f"STT failures: {out['failed_transcripts']}  refusals: {out['refused']}")
    for label, key in (("RAG-only (query -> answer)", "rag_only_ms"),
                       ("STT (Sarvam network)", "stt_ms"),
                       ("End-to-end voice", "end_to_end_ms")):
        p = out[key]
        lines.append(f"\n## {label}\n\nP50: {p['p50']} ms  P70: {p['p70']} ms  P100: {p['p100']} ms")
    lines.append("\n" + out.get("note", ""))
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
