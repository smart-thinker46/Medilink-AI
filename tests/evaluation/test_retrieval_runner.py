from medilink_ai.evaluation.retrieval_metrics import precision_at_k, recall_at_k, reciprocal_rank


def test_precision_at_5_uses_requested_denominator():
    assert precision_at_k(["A", "B", "C", "D", "E"], {"A", "C"}, 5) == 0.4


def test_recall_at_5():
    assert recall_at_k(["A", "B", "C", "D", "E"], {"A", "C", "F"}, 5) == 2 / 3


def test_reciprocal_rank_first_result():
    assert reciprocal_rank(["A", "B", "C"], {"A"}) == 1.0


def test_reciprocal_rank_third_result():
    assert reciprocal_rank(["A", "B", "C"], {"C"}) == 1 / 3


def test_reciprocal_rank_no_relevant_result():
    assert reciprocal_rank(["A", "B", "C"], {"D"}) == 0.0
