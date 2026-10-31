from medilink_ai.knowledge.hybrid_search import reciprocal_rank_score


def test_rrf_rewards_results_present_in_both_rankings():
    both = reciprocal_rank_score(1, 7)
    keyword_only = reciprocal_rank_score(1, None)
    assert both > keyword_only


def test_rrf_is_independent_of_missing_rank():
    assert reciprocal_rank_score(None, 1) == reciprocal_rank_score(1, None)
