from medilink_ai.evaluation.models import EvaluationResult
from medilink_ai.evaluation.release_gate import evaluate_release_gate


def test_critical_failure_blocks_release():
    result = EvaluationResult("KA-SEC", "ANSWER", severity="CRITICAL", passed=False, category="UNAUTHORIZED_ACCESS", failure_reasons=["cross-facility exposure"])
    gate = evaluate_release_gate([result])
    assert not gate.passed
    assert gate.critical_failures == ["KA-SEC"]


def test_passing_cases_release():
    assert evaluate_release_gate([EvaluationResult("KA-1", "ANSWER", severity="MEDIUM", passed=True)]).passed
