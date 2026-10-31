"""Authorized hybrid retrieval using database-filtered candidates and RRF."""
from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy.orm import Session

from .access import KnowledgeAccessContext
from .keyword_search import KeywordSearchService
from .reranking import ReciprocalRankFusion


def reciprocal_rank_score(keyword_rank: int | None, vector_rank: int | None, k: int = 60) -> float:
    return ReciprocalRankFusion(k).score(keyword_rank, vector_rank)
from .vector_search import VectorSearchService


@dataclass(frozen=True)
class HybridSearchResult:
    chunk_id: str
    chunk: object
    score: float
    keyword_rank: int | None
    vector_rank: int | None
    keyword_score: float = 0.0
    vector_similarity: float = 0.0

    @property
    def fusion_score(self) -> float:
        return self.score


class HybridSearchService:
    def __init__(self, session: Session, rrf_k: int = 60) -> None:
        self.keyword_search = KeywordSearchService(session)
        self.vector_search = VectorSearchService(session)
        self.fusion = ReciprocalRankFusion(rrf_k)

    def search(self, query: str, context: KnowledgeAccessContext, top_k: int = 5, candidate_limit: int | None = None) -> list[HybridSearchResult]:
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")
        limit = candidate_limit or max(top_k * 5, 20)
        if not 1 <= limit <= 250:
            raise ValueError("candidate_limit must be between 1 and 250")
        keyword = self.keyword_search.search(query, context, top_k=limit, candidate_limit=limit)
        vector = self.vector_search.search(query, context, top_k=limit, candidate_limit=limit)
        return [
            HybridSearchResult(
                item.chunk_id, item.chunk, item.fusion_score, item.keyword_rank,
                item.vector_rank, item.keyword_score, item.vector_similarity,
            )
            for item in self.fusion.fuse(keyword, vector)[:top_k]
        ]
