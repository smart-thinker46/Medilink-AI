from __future__ import annotations

from .exceptions import AuditWriteError
from .models import AuditEvent
from .sink import AuditSink

ALLOWED_METADATA_KEYS = frozenset({
    "route", "http_method", "application_version", "safety_decision", "output_validation_status",
    "routing_status", "evidence_count", "review_required", "stage_status",
})


class AuditService:
    def __init__(self, sink: AuditSink):
        self.sink = sink

    def record(self, event: AuditEvent) -> None:
        unknown = set(event.metadata) - ALLOWED_METADATA_KEYS
        if unknown:
            raise AuditWriteError("Audit metadata contains unapproved fields.")
        try:
            self.sink.append(event)
        except AuditWriteError:
            raise
        except Exception as exc:
            raise AuditWriteError("Audit event could not be durably recorded.") from exc
