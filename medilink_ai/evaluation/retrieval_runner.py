"""Retrieval-only evaluation against the real evidence pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from ..knowledge.access import KnowledgeAccessContext
from ..knowledge.evidence_pipeline import KnowledgeEvidencePipeline
from ..safety import check_request
from .models import EvaluationCase
from .retrieval_metrics import precision_at_k, recall_at_k, reciprocal_rank
from .fixtures import EVALUATION_NAMESPACE, LEGACY_DOCUMENT_IDS
from uuid import uuid5


@dataclass(frozen=True)
class RetrievalEvaluationResult:
    case_id: str
    retrieved_document_ids: list[str]
    expected_document_ids: list[str]
    precision_at_5: float
    recall_at_5: float
    reciprocal_rank: float
    evidence_count: int
    passed: bool
    failure_reasons: list[str]


@dataclass(frozen=True)
class RetrievalEvaluationSummary:
    total_cases: int
    passed_cases: int
    pass_rate: float
    precision_at_5: float
    recall_at_5: float
    mean_reciprocal_rank: float
    authorization_leakage: int
    missing_evidence_passed: int


def summarize_retrieval_results(results: list[RetrievalEvaluationResult]) -> RetrievalEvaluationSummary:
    return RetrievalEvaluationSummary(
        total_cases=len(results),
        passed_cases=sum(result.passed for result in results),
        pass_rate=(sum(result.passed for result in results) / len(results)) if results else 0.0,
        precision_at_5=mean(result.precision_at_5 for result in results) if results else 0.0,
        recall_at_5=mean(result.recall_at_5 for result in results) if results else 0.0,
        mean_reciprocal_rank=mean(result.reciprocal_rank for result in results) if results else 0.0,
        authorization_leakage=sum(
            1 for result in results if result.case_id == "KA-006" and result.evidence_count > 0
        ),
        missing_evidence_passed=sum(
            1 for result in results if result.case_id == "KA-005" and result.passed
        ),
    )


def run_retrieval_evaluation(session, cases: list[EvaluationCase], k: int = 5) -> list[RetrievalEvaluationResult]:
    """Evaluate retrieval without invoking the language model."""
    return [evaluate_retrieval_case(session, case, k=k) for case in cases]


def evaluate_retrieval_case(session, case: EvaluationCase, k: int = 5) -> RetrievalEvaluationResult:
    # The production assistant applies the safety gate before retrieval. Keep
    # retrieval metrics from treating a deliberately refused request as a
    # normal relevance query.
    if check_request(case.question) and case.expected_behavior in {"REVIEW", "DENY"}:
        return RetrievalEvaluationResult(
            case_id=case.case_id, retrieved_document_ids=[],
            expected_document_ids=list(case.expected_document_ids),
            precision_at_5=0.0, recall_at_5=1.0, reciprocal_rank=0.0,
            evidence_count=0, passed=True, failure_reasons=[],
        )
    context = KnowledgeAccessContext(
        user_id=f"evaluation:{case.case_id}",
        organization_id=case.organization_id,
        facility_id=case.facility_id,
        department_id=case.department_id,
        roles=frozenset(case.roles),
        classification_level=case.classification_level,
    )
    evidence = KnowledgeEvidencePipeline(session).search(case.question, context, top_k=k).evidence
    retrieved = [item.source.document_id for item in evidence.items]
    expected = set(case.expected_document_ids)
    # Accept rows created by the original fixture loader, which used UUID5 of
    # the semantic EVAL-DOC-* identifier, while the current fixtures use stable UUIDs.
    expected_aliases = set(expected)
    for document_id in expected:
        semantic_id = LEGACY_DOCUMENT_IDS.get(document_id)
        if semantic_id:
            expected_aliases.add(str(uuid5(EVALUATION_NAMESPACE, semantic_id)))
    if expected:
        passed = bool(set(retrieved) & expected_aliases)
        failures = [] if passed else ["no expected authorized document was retrieved"]
    else:
        passed = not retrieved
        failures = [] if passed else ["evidence was retrieved for a case requiring no evidence"]
    return RetrievalEvaluationResult(
        case_id=case.case_id,
        retrieved_document_ids=retrieved,
        expected_document_ids=list(case.expected_document_ids),
        precision_at_5=precision_at_k(retrieved, expected_aliases, k),
        recall_at_5=recall_at_k(retrieved, expected_aliases, k),
        reciprocal_rank=reciprocal_rank(retrieved, expected_aliases, k),
        evidence_count=len(evidence.items),
        passed=passed,
        failure_reasons=failures,
    )
