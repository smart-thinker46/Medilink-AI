from __future__ import annotations

from abc import ABC, abstractmethod

from .hybrid_search import HybridSearchResult


class EvidenceReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidates: list[HybridSearchResult], top_k: int = 5) -> list[HybridSearchResult]:
        raise NotImplementedError
