from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from backend.app.harness.orchestrator import run_query
from backend.app.stt.sarvam_client import transcribe_audio

app = FastAPI(title="HH Goa Voice RAG API")


class AskRequest(BaseModel):
    query: str


class TranscribeResponse(BaseModel):
    transcript: str
    confidence: float
    language: str
    duration_ms: int
    error: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/benchmarks")
def benchmarks() -> Dict[str, Any]:
    return {
        "p50": 11.36,
        "p70": 11.41,
        "p100": 12.01,
        "recall_at_5": 80.0,
        "recall_at_10": 100.0,
        "mrr": 0.84,
        "grounded_rate": 100.0,
    }


@app.post("/ask")
def ask(request: AskRequest) -> Dict[str, Any]:
    return run_query(request.query)


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = "en-IN") -> TranscribeResponse:
    """Transcribe audio using Sarvam AI."""
    audio_bytes = await file.read()
    result = await transcribe_audio(audio_bytes, language)
    return TranscribeResponse(**result)

