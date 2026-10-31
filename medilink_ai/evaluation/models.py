from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class EvaluationStage(str, Enum):
    AUTHORIZATION = "AUTHORIZATION"
    RETRIEVAL = "RETRIEVAL"
    EVIDENCE_ASSEMBLY = "EVIDENCE_ASSEMBLY"
    GENERATION = "GENERATION"
    VALIDATION = "VALIDATION"
    SAFETY = "SAFETY"
    PERFORMANCE = "PERFORMANCE"


class EvaluationFailureType(str, Enum):
    AUTHORIZATION_LEAKAGE = "AUTHORIZATION_LEAKAGE"
    WRONG_DOCUMENT = "WRONG_DOCUMENT"
    MISSING_DOCUMENT = "MISSING_DOCUMENT"
    INSUFFICIENT_EVIDENCE_FAILURE = "INSUFFICIENT_EVIDENCE_FAILURE"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    INVALID_CITATION = "INVALID_CITATION"
    WRONG_BEHAVIOR = "WRONG_BEHAVIOR"
    UNSAFE_RECOMMENDATION = "UNSAFE_RECOMMENDATION"
    PROMPT_INJECTION_SUCCESS = "PROMPT_INJECTION_SUCCESS"
    OUTPUT_VALIDATION_FAILURE = "OUTPUT_VALIDATION_FAILURE"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"

EvaluationCategory = Literal[
    "KNOWLEDGE", "PHARMACY", "BILLING", "REGISTRATION", "LABORATORY", "NURSING",
    "TERMINOLOGY", "MISSING_EVIDENCE", "CONFLICTING_EVIDENCE", "UNAUTHORIZED_ACCESS",
    "PROMPT_INJECTION", "SAFETY",
]
ExpectedBehavior = Literal["ANSWER", "ABSTAIN", "REVIEW", "DENY"]
EvaluationSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    category: EvaluationCategory
    question: str
    organization_id: str
    facility_id: str
    department_id: str | None
    roles: tuple[str, ...]
    classification_level: str
    expected_behavior: ExpectedBehavior
    expected_source_ids: tuple[str, ...] = ()
    expected_document_ids: tuple[str, ...] = ()
    expected_keywords: tuple[str, ...] = ()
    forbidden_keywords: tuple[str, ...] = ()
    notes: str = ""
    severity: EvaluationSeverity = "MEDIUM"


@dataclass
class EvaluationResult:
    case_id: str
    actual_behavior: str
    answer: str = ""
    actual_source_ids: list[str] = field(default_factory=list)
    latency_ms: float | None = None
    retrieval_score: float = 0.0
    citation_score: float = 0.0
    keyword_score: float = 0.0
    behavior_score: float = 0.0
    authorization_score: float = 0.0
    safety_score: float = 0.0
    passed: bool = False
    error: str | None = None
    severity: EvaluationSeverity = "MEDIUM"
    blocked_release: bool = False
    category: str = "UNKNOWN"
    failure_reasons: list[str] = field(default_factory=list)
    stage: EvaluationStage | None = None
    failure_type: EvaluationFailureType | None = None
    evaluation_version: str = "1.0"
    dataset_version: str = "1"


@dataclass(frozen=True)
class EvaluationSummary:
    total_cases: int
    passed_cases: int
    pass_rate: float
    retrieval_relevance: float
    citation_validity: float
    keyword_coverage: float
    authorization_accuracy: float
    safety_accuracy: float
    missing_evidence_abstention: float
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    gates_passed: bool
    gate_failures: tuple[str, ...] = ()
    critical_failures: tuple[str, ...] = ()
    release_status: str = "PASS"
