"""Authorization-aware semantic search."""
from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy.orm import Session

from .access import KnowledgeAccessContext
from .vector_search import VectorSearchResult, VectorSearchService


@dataclass
class AuthorizedVectorSearchResult:
    result: VectorSearchResult


class AuthorizedVectorSearchService:
    def __init__(self, session: Session):
        self.vector_search = VectorSearchService(session)

    def search(self, query: str, context: KnowledgeAccessContext, top_k: int = 5) -> list[AuthorizedVectorSearchResult]:
        candidate_limit = min(250, max(top_k * 5, 20))
        candidates = self.vector_search.search(query, context=context, top_k=candidate_limit, candidate_limit=candidate_limit)
        return [AuthorizedVectorSearchResult(result) for result in candidates[:top_k]]
