from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class AuditEventType(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    CONTEXT_VALIDATED = "CONTEXT_VALIDATED"
    PHI_PROTECTED = "PHI_PROTECTED"
    SAFETY_CLASSIFIED = "SAFETY_CLASSIFIED"
    MODEL_ROUTED = "MODEL_ROUTED"
    INFERENCE_COMPLETED = "INFERENCE_COMPLETED"
    OUTPUT_VALIDATED = "OUTPUT_VALIDATED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    REQUEST_COMPLETED = "REQUEST_COMPLETED"
    REQUEST_BLOCKED = "REQUEST_BLOCKED"
    REQUEST_FAILED = "REQUEST_FAILED"


class AuditSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    SECURITY = "SECURITY"
    ERROR = "ERROR"


class AuditOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class AuditEvent:
    event_type: AuditEventType
    request_id: str
    outcome: AuditOutcome
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    severity: AuditSeverity = AuditSeverity.INFO
    actor_id: str | None = None
    organization_id: str | None = None
    facility_id: str | None = None
    department_id: str | None = None
    module: str | None = None
    capability: str | None = None
    purpose_category: str | None = None
    patient_ref_hash: str | None = None
    encounter_ref_hash: str | None = None
    stage: str | None = None
    reason_codes: tuple[str, ...] = ()
    provider: str | None = None
    model_id: str | None = None
    model_name: str | None = None
    evidence_document_ids: tuple[str, ...] = ()
    evidence_chunk_ids: tuple[str, ...] = ()
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    prompt_fingerprint: str | None = None
    response_fingerprint: str | None = None
    metadata: dict[str, str | int | float | bool | None] = field(default_factory=dict)
