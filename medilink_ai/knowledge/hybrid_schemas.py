"""API contracts for hybrid knowledge retrieval."""
from __future__ import annotations

from pydantic import BaseModel, Field


class HybridSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)


class HybridSearchSource(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    version: str
    source_filename: str
    chunk_index: int
    hybrid_score: float
    keyword_rank: int | None = None
    vector_rank: int | None = None


class HybridSearchResponse(BaseModel):
    status: str
    query: str
    retrieval_method: str = "hybrid_rrf"
    results: list[HybridSearchSource]
