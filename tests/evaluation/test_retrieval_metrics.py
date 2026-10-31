from medilink_ai.evaluation.retrieval_metrics import precision_at_k, recall_at_k, reciprocal_rank


def test_retrieval_metrics():
    retrieved = ["S1", "S2", "S3"]
    expected = {"S1", "S3"}
    assert precision_at_k(retrieved, expected) == 2 / 3
    assert recall_at_k(retrieved, expected) == 1.0
    assert reciprocal_rank(retrieved, expected) == 1.0
