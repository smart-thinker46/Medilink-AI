from __future__ import annotations

from .db_models import GatewayAuditEventRecord
from .exceptions import AuditWriteError
from .models import AuditEvent


class PostgresAuditSink:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def append(self, event: AuditEvent) -> None:
        session = self.session_factory()
        try:
            session.add(GatewayAuditEventRecord(
                event_id=event.event_id, request_id=event.request_id, event_type=event.event_type.value,
                outcome=event.outcome.value, severity=event.severity.value, occurred_at=event.occurred_at,
                actor_id=event.actor_id, organization_id=event.organization_id, facility_id=event.facility_id,
                department_id=event.department_id, module=event.module, capability=event.capability,
                purpose_category=event.purpose_category, patient_ref_hash=event.patient_ref_hash,
                encounter_ref_hash=event.encounter_ref_hash, stage=event.stage, reason_codes=list(event.reason_codes),
                provider=event.provider, model_id=event.model_id, model_name=event.model_name,
                evidence_document_ids=list(event.evidence_document_ids), evidence_chunk_ids=list(event.evidence_chunk_ids),
                latency_ms=event.latency_ms, prompt_tokens=event.prompt_tokens, completion_tokens=event.completion_tokens,
                prompt_fingerprint=event.prompt_fingerprint, response_fingerprint=event.response_fingerprint,
                metadata_json=event.metadata,
            ))
            session.commit()
        except Exception as exc:
            session.rollback()
            raise AuditWriteError("Audit event could not be durably recorded.") from exc
        finally:
            session.close()
