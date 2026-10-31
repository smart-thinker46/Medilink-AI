from medilink_ai.gateway import AICapability
from medilink_ai.gateway.safety import AIActionType, AIRiskLevel, AISafetyDecision, AISafetyService


def test_knowledge_explanation_is_allowed():
    result = AISafetyService().classify(AICapability.KNOWLEDGE_ASK, "Explain the pharmacy POS reconciliation procedure")
    assert result.risk_level == AIRiskLevel.LOW
    assert result.decision == AISafetyDecision.ALLOW
    assert result.action_type == AIActionType.EXPLAIN


def test_patient_summary_requires_human_review():
    result = AISafetyService().classify(AICapability.PATIENT_SUMMARY, "Summarize this patient's current admission")
    assert result.risk_level == AIRiskLevel.MODERATE
    assert result.decision == AISafetyDecision.REVIEW_REQUIRED
    assert result.requires_human_review is True

