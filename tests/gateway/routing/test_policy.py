from medilink_ai.gateway import AICapability
from medilink_ai.gateway.routing import get_capability_routing_policy


def test_knowledge_has_routing_policy():
    policy = get_capability_routing_policy(AICapability.KNOWLEDGE_ASK)
    assert policy is not None
    assert policy.preferred_model_ids


def test_patient_summary_requires_specialized_approved_model():
    policy = get_capability_routing_policy(AICapability.PATIENT_SUMMARY)
    assert policy is not None
    assert policy.requires_human_review is True
    assert "patient-summary-model" in policy.preferred_model_ids

