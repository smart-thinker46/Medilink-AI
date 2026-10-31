from __future__ import annotations

from collections.abc import Iterable

from .grounding_models import ClaimEvaluation, ClaimSupport, GroundingEvaluation


def validate_citation_sources(citations: Iterable, available_source_ids: Iterable[str]) -> dict:
    available = set(available_source_ids)
    invalid = [citation.source_id for citation in citations if citation.source_id not in available]
    return {"valid": not invalid, "invalid_citations": invalid}


def calculate_grounding_score(claim_results: Iterable[ClaimEvaluation]) -> float:
    claims = list(claim_results)
    return sum(result.support == ClaimSupport.SUPPORTED for result in claims) / len(claims) if claims else 0.0


def evaluate_citations(citations: Iterable, available_source_ids: Iterable[str]) -> GroundingEvaluation:
    """Evaluate citation integrity; semantic entailment remains human-reviewed."""
    citations = list(citations)
    validity = validate_citation_sources(citations, available_source_ids)
    claims = [ClaimEvaluation(c.claim, ClaimSupport.SUPPORTED if citation.source_id in set(available_source_ids) else ClaimSupport.UNSUPPORTED, [citation.source_id], "Citation references an available evidence source." if citation.source_id in set(available_source_ids) else "Citation source is unavailable.") for c, citation in zip(citations, citations)]
    score = calculate_grounding_score(claims)
    return GroundingEvaluation(len(claims), sum(c.support == ClaimSupport.SUPPORTED for c in claims), 0, sum(c.support == ClaimSupport.UNSUPPORTED for c in claims), 0, score, validity["valid"], claims)
