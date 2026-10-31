"""Rank fusion for heterogeneous keyword and vector result scales."""
from __future__ import annotations

from dataclasses import dataclass

RRF_K = 60


@dataclass(frozen=True)
class RankedCandidate:
    chunk_id: str
    chunk: object
    keyword_rank: int | None
    vector_rank: int | None
    keyword_score: float
    vector_similarity: float
    fusion_score: float


class ReciprocalRankFusion:
    def __init__(self, smoothing_constant: int = RRF_K) -> None:
        if smoothing_constant <= 0:
            raise ValueError("smoothing_constant must be positive")
        self.smoothing_constant = smoothing_constant

    def score(self, keyword_rank: int | None, vector_rank: int | None) -> float:
        return sum(1 / (self.smoothing_constant + rank) for rank in (keyword_rank, vector_rank) if rank and rank > 0)

    def fuse(self, keyword_results: list, vector_results: list) -> list[RankedCandidate]:
        keyword = {str(item.chunk.id): (item, rank) for rank, item in enumerate(keyword_results, 1)}
        vector = {str(item.chunk.id): (item, rank) for rank, item in enumerate(vector_results, 1)}
        candidates: list[RankedCandidate] = []
        for chunk_id in set(keyword) | set(vector):
            k_item = keyword.get(chunk_id)
            v_item = vector.get(chunk_id)
            chunk = k_item[0].chunk if k_item else v_item[0].chunk
            k_rank = k_item[1] if k_item else None
            v_rank = v_item[1] if v_item else None
            candidates.append(RankedCandidate(
                chunk_id=chunk_id, chunk=chunk, keyword_rank=k_rank, vector_rank=v_rank,
                keyword_score=float(k_item[0].score) if k_item else 0.0,
                vector_similarity=float(v_item[0].similarity) if v_item else 0.0,
                fusion_score=self.score(k_rank, v_rank),
            ))
        return sorted(candidates, key=lambda item: (-item.fusion_score, item.chunk_id))
