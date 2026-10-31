from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievalCaseResult:
    case_id: str
    precision_at_5: float
    recall_at_5: float
    reciprocal_rank: float
    evidence_count: int
    passed: bool
    latency_seconds: float
    failure_reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RetrievalBenchmarkSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    mean_precision_at_5: float
    mean_recall_at_5: float
    mean_reciprocal_rank: float
    average_latency_seconds: float
    maximum_latency_seconds: float
    authorization_leakage_count: int
    missing_evidence_failures: int
    results_by_case: list[RetrievalCaseResult]

    @property
    def pass_rate(self) -> float:
        return self.passed_cases / self.total_cases if self.total_cases else 0.0
