from medilink_ai.gateway import AICapability, AuthenticatedPrincipal, GatewayAuthorizationService, GatewayDecisionStatus, GatewayRequest


def principal(*permissions, facilities=("facility-001",), departments=("clinical",)):
    return AuthenticatedPrincipal("doctor-001", "org-001", frozenset(facilities), frozenset(departments), frozenset({"DOCTOR"}), frozenset({"ai:use", *permissions, "patient:context:read"}))


def test_registry_rejects_patient_summary_from_pharmacy():
    request = GatewayRequest(capability=AICapability.PATIENT_SUMMARY, module="pharmacy", facility_id="facility-001", patient_id="patient-1", query="summary")
    decision = GatewayAuthorizationService().authorize(principal("ai:patient_summary"), request, patient_access_verified=True)
    assert decision.status == GatewayDecisionStatus.DENIED
    assert "MODULE_ACCESS_DENIED" in decision.reason_codes


def test_patient_access_is_denied_without_trusted_verification():
    request = GatewayRequest(capability=AICapability.PATIENT_SUMMARY, module="clinical", facility_id="facility-001", patient_id="patient-1", query="summary")
    decision = GatewayAuthorizationService().authorize(principal("ai:patient_summary"), request)
    assert decision.status == GatewayDecisionStatus.DENIED
    assert "PATIENT_ACCESS_NOT_VERIFIED" in decision.reason_codes


def test_verified_patient_access_can_be_allowed():
    request = GatewayRequest(capability=AICapability.PATIENT_SUMMARY, module="clinical", facility_id="facility-001", patient_id="patient-1", query="summary")
    decision = GatewayAuthorizationService().authorize(principal("ai:patient_summary"), request, patient_access_verified=True)
    assert decision.status == GatewayDecisionStatus.ALLOWED
