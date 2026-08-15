from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    language: str = "en"


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_strategy: str
    position: int
    token_count: int
    language: str
    text: str
    score: float


class QueryResponse(BaseModel):
    query: str
    retrieved_chunks: List[RetrievedChunk]
    scores: List[float]
    answer: str
    grounded: bool
    confidence: float
    latency_ms: int
    status: str = "ok"
    error: Optional[str] = None
    sources: List[str] = []


class QueryResultDict(Dict[str, Any]):
    pass
