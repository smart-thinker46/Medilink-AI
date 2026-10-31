from medilink_ai.gateway import AICapability
from medilink_ai.gateway.safety import AIActionType, AIRiskLevel, AISafetyDecision, AISafetyService


def test_safe_request_is_allowed():
    result = AISafetyService().classify(AICapability.KNOWLEDGE_ASK, "Explain the hospital billing procedure")
    assert result.decision == AISafetyDecision.ALLOW
    assert result.risk_level == AIRiskLevel.LOW


def test_clinical_draft_requires_review():
    result = AISafetyService().classify(AICapability.DOCUMENTATION_DRAFT, "Draft a clinical note from this encounter")
    assert result.decision == AISafetyDecision.REVIEW_REQUIRED
    assert result.requires_human_review is True


def test_critical_actions_are_denied():
    service = AISafetyService()
    for query, action in (
        ("Approve this patient's discharge", AIActionType.APPROVE),
        ("Authorize this medication", AIActionType.AUTHORIZE),
        ("Change the patient's balance to KES 0", AIActionType.MODIFY),
    ):
        result = service.classify(AICapability.PATIENT_SUMMARY, query)
        assert result.action_type == action
        assert result.risk_level == AIRiskLevel.CRITICAL
        assert result.decision == AISafetyDecision.DENY


def test_unknown_action_fails_conservatively():
    result = AISafetyService().classify(AICapability.KNOWLEDGE_ASK, "Perform an unfamiliar operation")
    assert result.risk_level == AIRiskLevel.HIGH
    assert result.decision == AISafetyDecision.REVIEW_REQUIRED
    assert result.requires_human_review is True

