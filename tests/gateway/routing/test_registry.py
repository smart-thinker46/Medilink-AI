from medilink_ai.gateway.routing import ModelRegistry


def test_default_registry_contains_development_model():
    registry = ModelRegistry()
    assert registry.all()
    assert registry.get("knowledge-small") is not None

