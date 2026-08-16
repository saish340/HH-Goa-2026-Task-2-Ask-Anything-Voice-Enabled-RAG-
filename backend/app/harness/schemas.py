from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1024)
    language: str | None = None


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
    normalized_query: str = ""
    language: str = "en"
    retrieved_chunks: List[RetrievedChunk] = []
    scores: List[float] = []
    answer: str = ""
    grounded: bool = False
    grounding_label: str = "UNSUPPORTED"
    grounding_score: float = 0.0
    confidence: float = 0.0
    latency_ms: int = 0
    per_stage_ms: Dict[str, float] = {}
    strategy_used: str = "all"
    generation_method: str = "extractive"  # extractive | llm
    degraded: bool = False
    status: str = "ok"  # ok | refused | error
    error: Optional[str] = None
    sources: List[str] = []
    version: str = "2.0"


class QueryResultDict(Dict[str, Any]):
    pass