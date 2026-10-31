from medilink_ai.gateway.audit import build_gateway_audit_event
from medilink_ai.gateway.audit.models import AuditEventType, AuditOutcome


def test_builder_pseudonymizes_patient_reference(monkeypatch):
    monkeypatch.setenv("MEDILINK_AUDIT_HMAC_KEY", "development-test-key-with-more-than-32-characters")
    event = build_gateway_audit_event(event_type=AuditEventType.AUTHORIZATION, request_id="request-001", outcome=AuditOutcome.SUCCESS, actor_id="doctor-001", organization_id="org-001", facility_id="facility-001", patient_id="patient-001", stage="AUTHORIZATION", reason_codes=("AUTHORIZATION_PASSED",))
    assert event.request_id == "request-001"
    assert event.patient_ref_hash and "patient-001" not in event.patient_ref_hash

