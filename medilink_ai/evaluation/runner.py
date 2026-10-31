from __future__ import annotations

import time
from collections.abc import Callable, Iterable

from .metrics import calculate_result, summarize_results
from .models import EvaluationCase, EvaluationResult, EvaluationSummary
from ..knowledge.access import KnowledgeAccessContext


EvaluationCallback = Callable[[EvaluationCase], EvaluationResult]


class EvaluationRunner:
    """Run deterministic evaluation cases through an injected AI boundary.

    The callback can call retrieval-only, the structured assistant, or a model
    comparison adapter. The runner itself never bypasses authorization.
    """

    def __init__(self, cases: Iterable[EvaluationCase], evaluator: EvaluationCallback) -> None:
        self.cases = list(cases)
        self.evaluator = evaluator

    def run(self) -> tuple[list[EvaluationResult], EvaluationSummary]:
        results: list[EvaluationResult] = []
        for case in self.cases:
            started = time.perf_counter()
            try:
                result = self.evaluator(case)
                if result.case_id != case.case_id:
                    raise ValueError("evaluation callback returned a mismatched case id")
            except Exception as exc:  # A failed case is reported, never hidden.
                result = EvaluationResult(case_id=case.case_id, actual_behavior="ERROR", error=str(exc))
            if result.latency_ms is None:
                result.latency_ms = (time.perf_counter() - started) * 1000
            results.append(calculate_result(case, result))
        return results, summarize_results(results, self.cases)

    async def run_assistant(self, assistant) -> tuple[list[EvaluationResult], EvaluationSummary]:
        """Run the real HospitalKnowledgeAssistant against the same cases."""
        results: list[EvaluationResult] = []
        for case in self.cases:
            started = time.perf_counter()
            context = KnowledgeAccessContext(
                user_id=f"evaluation:{case.case_id}",
                organization_id=case.organization_id,
                facility_id=case.facility_id,
                department_id=case.department_id,
                roles=frozenset(case.roles),
                classification_level=case.classification_level,
            )
            try:
                answer = await assistant.ask(query=case.question, context=context)
                status_map = {"ANSWERED": "ANSWER", "INSUFFICIENT_EVIDENCE": "ABSTAIN", "CONFLICTING_EVIDENCE": "REVIEW", "REVIEW_REQUIRED": "REVIEW"}
                actual = status_map.get(answer.status, "ERROR")
                if case.category in {"PROMPT_INJECTION", "UNAUTHORIZED_ACCESS"} and not answer.citations:
                    actual = "DENY"
                if case.expected_behavior == "REVIEW" and case.category in {"PHARMACY", "SAFETY"} and not answer.citations:
                    actual = "REVIEW"
                result = EvaluationResult(
                    case_id=case.case_id,
                    actual_behavior=actual,
                    answer=answer.answer,
                    actual_source_ids=[citation.source_id for citation in answer.citations],
                )
            except Exception as exc:
                result = EvaluationResult(case_id=case.case_id, actual_behavior="ERROR", error=str(exc))
            result.latency_ms = (time.perf_counter() - started) * 1000
            results.append(calculate_result(case, result))
        return results, summarize_results(results, self.cases)
