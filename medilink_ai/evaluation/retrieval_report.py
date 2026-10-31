from __future__ import annotations

from statistics import mean

from .retrieval_report_models import RetrievalBenchmarkSummary, RetrievalCaseResult


def summarize_retrieval_results(
    results: list[RetrievalCaseResult],
    authorization_leakage_count: int = 0,
    missing_evidence_failures: int = 0,
) -> RetrievalBenchmarkSummary:
    applicable = [result for result in results if result.evidence_count or result.recall_at_5 > 0]
    return RetrievalBenchmarkSummary(
        total_cases=len(results),
        passed_cases=sum(result.passed for result in results),
        failed_cases=sum(not result.passed for result in results),
        mean_precision_at_5=mean(result.precision_at_5 for result in applicable) if applicable else 0.0,
        mean_recall_at_5=mean(result.recall_at_5 for result in applicable) if applicable else 0.0,
        mean_reciprocal_rank=mean(result.reciprocal_rank for result in applicable) if applicable else 0.0,
        average_latency_seconds=mean(result.latency_seconds for result in results) if results else 0.0,
        maximum_latency_seconds=max((result.latency_seconds for result in results), default=0.0),
        authorization_leakage_count=authorization_leakage_count,
        missing_evidence_failures=missing_evidence_failures,
        results_by_case=list(results),
    )
