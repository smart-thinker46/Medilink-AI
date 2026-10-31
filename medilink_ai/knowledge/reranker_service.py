from functools import lru_cache

from .local_reranker import LocalEvidenceReranker
from .reranker_base import EvidenceReranker


@lru_cache(maxsize=1)
def get_evidence_reranker() -> EvidenceReranker:
    return LocalEvidenceReranker()
