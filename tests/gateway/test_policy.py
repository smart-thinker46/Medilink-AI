import pytest
from pydantic import ValidationError

from medilink_ai.gateway import AICapability, AuthenticatedPrincipal, GatewayDecisionStatus, GatewayRequest, authorize_gateway_request


@pytest.fixture
def principal():
    return AuthenticatedPrincipal(
        subject_id="doctor-001", organization_id="org-001", facility_ids=frozenset({"facility-001"}),
        department_ids=frozenset({"clinical"}), roles=frozenset({"DOCTOR"}),
        permissions=frozenset({"ai:use", "ai:capability:knowledge.ask", "patient:context:read"}),
    )


def test_authorized_knowledge_request_is_allowed(principal):
    request = GatewayRequest(capability=AICapability.KNOWLEDGE_ASK, module="clinical", facility_id="facility-001", department_id="clinical", query="What is the policy?")
    assert authorize_gateway_request(principal, request).status == GatewayDecisionStatus.ALLOWED


def test_identity_and_roles_cannot_be_supplied_by_request_body():
    fields = GatewayRequest.model_fields
    assert "organization_id" not in fields
    assert "user_id" not in fields
    assert "roles" not in fields
    assert "permissions" not in fields


def test_wrong_facility_is_denied(principal):
    request = GatewayRequest(capability=AICapability.KNOWLEDGE_ASK, module="clinical", facility_id="facility-999", query="policy")
    decision = authorize_gateway_request(principal, request)
    assert decision.status == GatewayDecisionStatus.DENIED
    assert "FACILITY_ACCESS_DENIED" in decision.reason_codes


def test_patient_summary_requires_patient_and_permission(principal):
    with pytest.raises(ValidationError):
        GatewayRequest(capability=AICapability.PATIENT_SUMMARY, module="clinical", facility_id="facility-001", query="summary")
    request = GatewayRequest(capability=AICapability.PATIENT_SUMMARY, module="clinical", facility_id="facility-001", patient_id="patient-1", query="summary")
    assert authorize_gateway_request(principal, request).status == GatewayDecisionStatus.DENIED
