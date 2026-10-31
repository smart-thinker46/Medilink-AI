import asyncio

import pytest

from medilink_ai.gateway.audit import AuditService, InMemoryAuditSink
from medilink_ai.gateway.orchestration import GatewayExecutionStatus

from .conftest import make_orchestrator
from .fakes import FakeExecutor, FailingAuditService


def test_request_id_is_propagated_to_audit(authorized_principal, knowledge_request, monkeypatch):
    monkeypatch.setenv("MEDILINK_AUDIT_HMAC_KEY", "integration-test-key-with-more-than-32-characters")
    sink = InMemoryAuditSink(); executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(executor=executor, audit=AuditService(sink)).execute(principal=authorized_principal, request=knowledge_request))
    assert result.status == GatewayExecutionStatus.COMPLETED
    assert sink.events and all(event.request_id == str(knowledge_request.request_id) for event in sink.events)
    assert sink.events[0].event_type.value == "REQUEST_RECEIVED"
    assert sink.events[-1].event_type.value == "REQUEST_COMPLETED"


def test_mandatory_audit_failure_fails_closed(authorized_principal, knowledge_request):
    executor = FakeExecutor()
    with pytest.raises(Exception):
        asyncio.run(make_orchestrator(executor=executor, audit=FailingAuditService()).execute(principal=authorized_principal, request=knowledge_request))
    assert executor.calls == []
