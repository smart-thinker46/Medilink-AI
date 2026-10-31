from medilink_ai.gateway import AICapability
from medilink_ai.gateway.phi import PHILevel, get_phi_policy


def test_knowledge_policy_is_restrictive():
    policy = get_phi_policy(AICapability.KNOWLEDGE_ASK)
    assert policy.allow_patient_context is False
    assert policy.allow_direct_identifiers is False
    assert policy.allow_clinical_content is False
    assert policy.require_minimization is True


def test_patient_summary_allows_clinical_context_but_not_direct_identifiers():
    policy = get_phi_policy(AICapability.PATIENT_SUMMARY)
    assert policy.allow_patient_context is True
    assert policy.allow_clinical_content is True
    assert policy.allow_direct_identifiers is False
    assert policy.maximum_level == PHILevel.HIGH

