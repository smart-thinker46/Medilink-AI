from types import SimpleNamespace

from medilink_ai.knowledge.reranking import ReciprocalRankFusion


def result(chunk_id: str, score: float, similarity: float):
    return SimpleNamespace(chunk=SimpleNamespace(id=chunk_id), score=score, similarity=similarity)


def test_rrf_combines_keyword_and_vector_rankings():
    ranked = ReciprocalRankFusion().fuse(
        [result("a", 10, 0), result("b", 8, 0)],
        [result("b", 0, .95), result("a", 0, .7)],
    )
    assert ranked[0].chunk_id in {"a", "b"}
    assert all(item.fusion_score > 0 for item in ranked)
