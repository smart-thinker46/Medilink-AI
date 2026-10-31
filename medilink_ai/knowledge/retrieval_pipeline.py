from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy.orm import Session

from .access import KnowledgeAccessContext
from .hybrid_search import HybridSearchResult, HybridSearchService
from .reranker_service import get_evidence_reranker


@dataclass(frozen=True)
class RetrievalPipelineResult:
    candidates: list[HybridSearchResult]


class KnowledgeRetrievalPipeline:
    def __init__(self, session: Session) -> None:
        self.hybrid_search = HybridSearchService(session)
        self.reranker = get_evidence_reranker()

    def search(self, query: str, context: KnowledgeAccessContext, candidate_limit: int = 20, top_k: int = 5) -> RetrievalPipelineResult:
        candidates = self.hybrid_search.search(query, context, top_k=candidate_limit, candidate_limit=candidate_limit)
        return RetrievalPipelineResult(self.reranker.rerank(query, candidates, top_k=top_k))
