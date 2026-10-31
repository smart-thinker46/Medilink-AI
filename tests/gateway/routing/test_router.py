import pytest

from medilink_ai.gateway import AICapability
from medilink_ai.gateway.routing import (
    ModelAvailability, ModelCapability, ModelDefinition, ModelNotFoundError,
    ModelRegistry, ModelRouter, ModelRoutingRequest, RoutingDecisionStatus,
)


def test_knowledge_request_routes_to_registered_model():
    decision = ModelRouter(ModelRegistry()).route(ModelRoutingRequest(AICapability.KNOWLEDGE_ASK, minimum_output_tokens=200, requires_json=True))
    assert decision.status == RoutingDecisionStatus.ROUTED
    assert decision.model and decision.model.model_id == "knowledge-small"


def test_unknown_explicit_model_is_rejected():
    with pytest.raises(ModelNotFoundError):
        ModelRouter(ModelRegistry()).route(ModelRoutingRequest(AICapability.KNOWLEDGE_ASK, requested_model_id="untrusted-model"))


def test_sensitive_capability_does_not_fallback_to_general_model():
    decision = ModelRouter(ModelRegistry()).route(ModelRoutingRequest(AICapability.PATIENT_SUMMARY))
    assert decision.status == RoutingDecisionStatus.BLOCKED
    assert decision.model is None


def test_second_approved_model_is_marked_fallback():
    models = (
        ModelDefinition("knowledge-small", "ollama", "small", frozenset({ModelCapability.KNOWLEDGE}), priority=10, supports_json=True, availability=ModelAvailability.UNAVAILABLE),
        ModelDefinition("knowledge-medium", "ollama", "medium", frozenset({ModelCapability.KNOWLEDGE}), priority=20, supports_json=True),
    )
    decision = ModelRouter(ModelRegistry(models)).route(ModelRoutingRequest(AICapability.KNOWLEDGE_ASK))
    assert decision.status == RoutingDecisionStatus.FALLBACK
    assert decision.fallback_used is True
    assert decision.model and decision.model.model_id == "knowledge-medium"

