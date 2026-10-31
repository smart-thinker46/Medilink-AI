import pytest

from medilink_ai.gateway import AICapability
from medilink_ai.gateway.phi import (
    AIContextField, PHILevel, PHIProcessingDecision, PHIProtectionService,
)
from medilink_ai.gateway.phi.exceptions import PHIPolicyViolation


def test_clean_knowledge_request_is_allowed():
    decision = PHIProtectionService().evaluate(AICapability.KNOWLEDGE_ASK, "What is the pharmacy POS procedure?")
    assert decision.allowed is True
    assert decision.level == PHILevel.NONE


def test_knowledge_phone_is_minimized_before_model_processing():
    result = PHIProtectionService().protect_text(AICapability.KNOWLEDGE_ASK, "Contact +254712345678.")
    assert "+254712345678" not in result.protected_text


def test_restricted_identifier_blocks_knowledge_capability():
    service = PHIProtectionService()
    decision = service.evaluate(AICapability.KNOWLEDGE_ASK, "National ID: 12345678")
    assert decision.allowed is False
    assert decision.reason_code == "PHI_LEVEL_EXCEEDS_CAPABILITY_POLICY"
    with pytest.raises(PHIPolicyViolation):
        service.protect_text(AICapability.KNOWLEDGE_ASK, "National ID: 12345678")


def test_patient_summary_can_process_high_phi_text():
    decision = PHIProtectionService().evaluate(AICapability.PATIENT_SUMMARY, "MRN: MRN-001234")
    assert decision.allowed is True


def test_structured_fields_are_minimized_by_explicit_allowlist():
    fields = (
        AIContextField("patient.name", "Ada", PHILevel.HIGH),
        AIContextField("patient.age", 42, PHILevel.MODERATE),
        AIContextField("billing.balance", 10, PHILevel.HIGH),
    )
    protected = PHIProtectionService().protect_fields(AICapability.PATIENT_SUMMARY, fields, frozenset({"patient.age"}))
    assert [field.name for field in protected.allowed_fields] == ["patient.age"]

