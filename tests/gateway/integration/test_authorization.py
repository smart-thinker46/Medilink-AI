import asyncio

from medilink_ai.gateway import AuthenticatedPrincipal
from medilink_ai.gateway.orchestration import GatewayExecutionStatus

from .conftest import make_orchestrator
from .fakes import FakeExecutor


def test_wrong_facility_never_reaches_executor(other_facility_principal, patient_summary_request):
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(executor=executor).execute(principal=other_facility_principal, request=patient_summary_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert "FACILITY_ACCESS_DENIED" in result.reason_codes
    assert executor.calls == []


def test_missing_capability_permission_is_denied(authorized_principal, patient_summary_request):
    principal = AuthenticatedPrincipal(authorized_principal.subject_id, authorized_principal.organization_id, authorized_principal.facility_ids, authorized_principal.department_ids, authorized_principal.roles, frozenset({"ai:use", "patient:context:read"}))
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(executor=executor).execute(principal=principal, request=patient_summary_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert "CAPABILITY_ACCESS_NOT_GRANTED" in result.reason_codes
    assert executor.calls == []


def test_wrong_department_is_denied(authorized_principal, knowledge_request):
    request = knowledge_request.model_copy(update={"department_id": "billing"})
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(executor=executor).execute(principal=authorized_principal, request=request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert "DEPARTMENT_ACCESS_DENIED" in result.reason_codes
    assert executor.calls == []


def test_client_cannot_supply_identity_fields():
    from pydantic import ValidationError
    try:
        from medilink_ai.gateway import GatewayRequest
        GatewayRequest(capability="knowledge.ask", module="clinical", facility_id="facility-001", query="x", user_id="attacker", roles=["ADMIN"])
    except ValidationError:
        return
    raise AssertionError("GatewayRequest accepted client-supplied identity")
