from medilink_ai.evaluation.retrieval_report import summarize_retrieval_results
from medilink_ai.evaluation.retrieval_report_models import RetrievalCaseResult


def test_retrieval_summary_aggregates_metrics():
    summary = summarize_retrieval_results([
        RetrievalCaseResult("R-001", .8, 1.0, 1.0, 5, True, .5),
        RetrievalCaseResult("R-002", .6, .5, .5, 5, False, 1.0),
    ])
    assert summary.total_cases == 2
    assert summary.failed_cases == 1
    assert summary.mean_precision_at_5 == .7
    assert summary.pass_rate == .5
