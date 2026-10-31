import pytest

from medilink_ai.gateway.audit import AuditService, InMemoryAuditSink
from medilink_ai.gateway.audit.exceptions import AuditWriteError
from medilink_ai.gateway.audit.models import AuditEvent, AuditEventType, AuditOutcome


def event(metadata=None):
    return AuditEvent(AuditEventType.REQUEST_RECEIVED, "request-001", AuditOutcome.SUCCESS, metadata=metadata or {})


def test_audit_service_records_event():
    sink = InMemoryAuditSink(); AuditService(sink).record(event())
    assert len(sink.events) == 1 and sink.events[0].request_id == "request-001"


def test_audit_service_rejects_unapproved_metadata():
    with pytest.raises(AuditWriteError):
        AuditService(InMemoryAuditSink()).record(event({"patient_name": "should never be stored"}))


def test_audit_write_failure_is_propagated():
    class FailingSink:
        def append(self, event): raise RuntimeError("database down")
    with pytest.raises(AuditWriteError):
        AuditService(FailingSink()).record(event())

