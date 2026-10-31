from pathlib import Path

from medilink_ai.evaluation.dataset import load_evaluation_dataset


def test_controlled_dataset_loads():
    path = Path(__file__).parent / "datasets" / "knowledge_assistant_v1.json"
    cases = load_evaluation_dataset(path)
    assert len(cases) == 12
    assert cases[0].expected_behavior == "ANSWER"


def test_critical_cases_have_expected_behavior():
    path = Path(__file__).parent / "datasets" / "knowledge_assistant_v1.json"
    cases = load_evaluation_dataset(path)
    critical = [case for case in cases if case.severity == "CRITICAL"]
    assert critical
    assert all(case.expected_behavior in {"DENY", "REVIEW", "ABSTAIN", "ANSWER"} for case in critical)
