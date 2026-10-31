from __future__ import annotations

from .hashing import hash_audit_reference
from .models import AuditEvent, AuditEventType, AuditOutcome, AuditSeverity


def build_gateway_audit_event(*, event_type: AuditEventType, request_id: str, outcome: AuditOutcome,
    actor_id: str | None = None, organization_id: str | None = None, facility_id: str | None = None,
    department_id: str | None = None, module: str | None = None, capability: str | None = None,
    purpose_category: str | None = None, patient_id: str | None = None, encounter_id: str | None = None,
    stage: str | None = None, reason_codes: tuple[str, ...] = (), severity: AuditSeverity = AuditSeverity.INFO,
    provider: str | None = None, model_id: str | None = None, model_name: str | None = None,
    evidence_document_ids: tuple[str, ...] = (), evidence_chunk_ids: tuple[str, ...] = (),
    latency_ms: float | None = None, prompt_tokens: int | None = None, completion_tokens: int | None = None,
    prompt_fingerprint: str | None = None, response_fingerprint: str | None = None,
    metadata: dict[str, str | int | float | bool | None] | None = None) -> AuditEvent:
    return AuditEvent(
        event_type=event_type, request_id=request_id, outcome=outcome, actor_id=actor_id,
        organization_id=organization_id, facility_id=facility_id, department_id=department_id,
        module=module, capability=capability, purpose_category=purpose_category,
        patient_ref_hash=hash_audit_reference(patient_id, reference_type="PATIENT"),
        encounter_ref_hash=hash_audit_reference(encounter_id, reference_type="ENCOUNTER"),
        stage=stage, reason_codes=tuple(reason_codes), severity=severity, provider=provider,
        model_id=model_id, model_name=model_name, evidence_document_ids=tuple(evidence_document_ids),
        evidence_chunk_ids=tuple(evidence_chunk_ids), latency_ms=latency_ms, prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens, prompt_fingerprint=prompt_fingerprint,
        response_fingerprint=response_fingerprint, metadata=dict(metadata or {}),
    )
