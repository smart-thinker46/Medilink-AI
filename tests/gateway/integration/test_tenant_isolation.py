import asyncio

from medilink_ai.gateway import AuthenticatedPrincipal
from medilink_ai.gateway.orchestration import GatewayExecutionStatus

from .conftest import make_orchestrator
from .fakes import FakeContextService, FakeExecutor


def test_cross_organization_request_is_blocked(authorized_principal, patient_summary_request):
    principal = AuthenticatedPrincipal(authorized_principal.subject_id, "org-002", frozenset({"facility-001"}), authorized_principal.department_ids, authorized_principal.roles, authorized_principal.permissions)
    executor = FakeExecutor()
    # The authoritative context adapter would return a tenant mismatch; the
    # integration double models that fail-closed response here.
    result = asyncio.run(make_orchestrator(context=FakeContextService(error=RuntimeError("cross-organization context")), executor=executor).execute(principal=principal, request=patient_summary_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert executor.calls == []
