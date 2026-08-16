from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.config import BENCH_DIR, DATA_DIR
from backend.app.harness.orchestrator import run_query, warmup
from backend.app.harness.schemas import QueryRequest, QueryResponse
from backend.app.stt.sarvam_client import transcribe_audio

app = FastAPI(title="HH Goa Voice RAG API")


class AskRequest(BaseModel):
    query: str
    language: str | None = None
    tier: str = "fast"  # fast (extractive) | llm


class TranscribeResponse(BaseModel):
    transcript: str
    confidence: float
    language: str
    duration_ms: int
    error: str | None = None


@app.on_event("startup")
def _startup_warmup() -> None:
    warmup()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/benchmarks")
def benchmarks() -> Dict[str, Any]:
    """Latest measured numbers (or empty defaults if not yet benchmarked)."""
    payload: Dict[str, Any] = {"available": False}
    latency_path = BENCH_DIR / "reports" / "latency.json"
    quality_path = BENCH_DIR / "reports" / "quality.json"
    if latency_path.exists():
        payload.update(json.loads(latency_path.read_text(encoding="utf-8")))
        payload["available"] = True
    if quality_path.exists():
        payload["quality"] = json.loads(quality_path.read_text(encoding="utf-8"))
    return payload


@app.get("/stats")
def stats() -> Dict[str, Any]:
    """Index statistics for the Stats page."""
    meta_path = DATA_DIR / "index_meta.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return {
        "corpus_passages": meta.get("passages", 0),
        "chunks": meta.get("chunks", 0),
        "per_strategy": meta.get("per_strategy", {}),
        "embedding_dim": meta.get("embedding_dim", 0),
    }


@app.post("/ask")
def ask(request: AskRequest) -> Dict[str, Any]:
    try:
        result = run_query(request.query, language=request.language, tier=request.tier)
        return QueryResponse(**result).model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"pipeline error: {exc}") from exc


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = "en-IN") -> TranscribeResponse:
    """Transcribe audio using Sarvam AI (retries built into the client)."""
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload")
    result = await transcribe_audio(audio_bytes, language)
    return TranscribeResponse(**result)