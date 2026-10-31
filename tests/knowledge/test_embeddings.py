from medilink_ai.knowledge.embeddings import get_embedding_service


def test_embedding_dimension():
    service = get_embedding_service()
    vector = service.embed_text("Patient registration requires verification.")
    assert len(vector) == service.dimension


def test_embedding_values_are_numeric():
    vector = get_embedding_service().embed_text("Hospital billing policy.")
    assert all(isinstance(value, float) for value in vector)


def test_similar_text_has_nonzero_similarity():
    service = get_embedding_service()
    score = service.similarity(
        "How do we prevent duplicate patient records?",
        "How can we avoid creating duplicate patient registrations?",
    )
    assert score > 0
