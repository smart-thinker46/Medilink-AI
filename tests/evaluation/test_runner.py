from medilink_ai.evaluation.dataset import load_evaluation_dataset
from medilink_ai.evaluation.models import EvaluationResult
from medilink_ai.evaluation.runner import EvaluationRunner


def test_critical_failure_blocks_release():
    cases = load_evaluation_dataset("tests/evaluation/datasets/knowledge_assistant_v1.json")

    def evaluate(case):
        # Deliberately fail one critical security case to verify the gate.
        return EvaluationResult(case.case_id, "ANSWER", "unsafe answer", ["S999"])

    results, summary = EvaluationRunner(cases, evaluate).run()
    assert any(result.blocked_release for result in results)
    assert summary.release_status == "BLOCKED"
    assert not summary.gates_passed
