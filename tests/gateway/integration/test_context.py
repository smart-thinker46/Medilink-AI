import asyncio

from medilink_ai.gateway.orchestration import GatewayExecutionStatus

from .conftest import make_orchestrator
from .fakes import FakeContextService, FakeExecutor


def test_context_failure_blocks_before_model(authorized_principal, patient_summary_request):
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(context=FakeContextService(error=RuntimeError("context unavailable")), executor=executor).execute(principal=authorized_principal, request=patient_summary_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert result.reason_codes == ("CONTEXT_VALIDATION_FAILED",)
    assert executor.calls == []


def test_context_service_receives_only_after_authorization(authorized_principal, patient_summary_request):
    context = FakeContextService()
    other = authorized_principal.__class__(authorized_principal.subject_id, authorized_principal.organization_id, frozenset({"facility-002"}), authorized_principal.department_ids, authorized_principal.roles, authorized_principal.permissions)
    asyncio.run(make_orchestrator(context=context).execute(principal=other, request=patient_summary_request))
    assert context.calls == []
