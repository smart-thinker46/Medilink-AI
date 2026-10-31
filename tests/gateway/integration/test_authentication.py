import asyncio

from medilink_ai.gateway.orchestration import GatewayExecutionStatus

from .conftest import make_orchestrator
from .fakes import FakeExecutor


def test_missing_identity_blocks_before_executor(knowledge_request):
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(executor=executor).execute(principal=None, request=knowledge_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert "AUTHENTICATION_FAILED" in result.reason_codes
    assert executor.calls == []
