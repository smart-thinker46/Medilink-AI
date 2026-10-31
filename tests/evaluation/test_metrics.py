from medilink_ai.evaluation.metrics import calculate_keyword_score, calculate_citation_score


def test_metrics_measure_coverage():
    assert calculate_keyword_score("Pharmacy sales and payment", ["pharmacy", "sales", "payment"]) == 1
    assert calculate_citation_score(["S1"], ["S1"]) == 1
    assert calculate_citation_score(["S1"], ["S9"]) == 0
