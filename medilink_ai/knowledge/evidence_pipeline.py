from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy.orm import Session

from .access import KnowledgeAccessContext
from .evidence_assembler import EvidenceAssembler
from .evidence_models import EvidenceBundle
from .retrieval_pipeline import KnowledgeRetrievalPipeline


@dataclass(frozen=True)
class EvidencePipelineResult:
    evidence: EvidenceBundle


class KnowledgeEvidencePipeline:
    def __init__(self, session: Session, assembler: EvidenceAssembler | None = None) -> None:
        self.retrieval = KnowledgeRetrievalPipeline(session)
        self.assembler = assembler or EvidenceAssembler()

    def search(self, query: str, context: KnowledgeAccessContext, top_k: int = 5, candidate_limit: int = 20) -> EvidencePipelineResult:
        ranked = self.retrieval.search(query, context, candidate_limit=candidate_limit, top_k=top_k)
        return EvidencePipelineResult(self.assembler.assemble(query, ranked.candidates))
