from __future__ import annotations

from dataclasses import dataclass

from .models import EvaluationResult


@dataclass(frozen=True)
class ReleaseGateResult:
    passed: bool
    critical_failures: list[str]
    high_failures: list[str]
    reasons: list[str]
    inconclusive: list[str] = None


def evaluate_release_gate(results: list[EvaluationResult]) -> ReleaseGateResult:
    critical: list[str] = []
    high: list[str] = []
    reasons: list[str] = []
    inconclusive: list[str] = []
    for result in results:
        if result.passed:
            continue
        description = f"{result.case_id} ({result.category}): " + "; ".join(result.failure_reasons or ["evaluation case failed"])
        if result.severity == "CRITICAL":
            critical.append(result.case_id)
            reasons.append("CRITICAL SECURITY/SAFETY FAILURE — " + description)
        elif result.severity == "HIGH":
            high.append(result.case_id)
            reasons.append("HIGH-SEVERITY FAILURE — " + description)
        else:
            reasons.append("Evaluation failure — " + description)
        if result.actual_behavior == "ERROR" or result.error:
            inconclusive.append(result.case_id)
            reasons.append("INCONCLUSIVE — evaluation infrastructure/provider error: " + description)
    return ReleaseGateResult(not critical and not high and not inconclusive, critical, high, reasons, inconclusive)
