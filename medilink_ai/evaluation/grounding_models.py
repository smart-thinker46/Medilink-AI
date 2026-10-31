from dataclasses import dataclass
from enum import Enum


class ClaimSupport(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


@dataclass(frozen=True)
class ClaimEvaluation:
    claim: str
    support: ClaimSupport
    source_ids: list[str]
    explanation: str


@dataclass(frozen=True)
class GroundingEvaluation:
    total_claims: int
    supported_claims: int
    partially_supported_claims: int
    unsupported_claims: int
    contradicted_claims: int
    grounding_score: float
    passed: bool
    claim_results: list[ClaimEvaluation]
