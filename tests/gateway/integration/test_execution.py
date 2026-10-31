import asyncio

from medilink_ai.gateway.orchestration import GatewayExecutionStatus

from .conftest import make_orchestrator
from .fakes import FakeExecutor


def test_provider_failure_returns_failed_without_hmis_failure(authorized_principal, knowledge_request):
    executor = FakeExecutor(error=RuntimeError("provider unavailable"))
    result = asyncio.run(make_orchestrator(executor=executor).execute(principal=authorized_principal, request=knowledge_request))
    assert result.status == GatewayExecutionStatus.FAILED
    assert result.reason_codes == ("AI_EXECUTION_FAILED",)
