import asyncio

from medilink_ai.gateway.orchestration import GatewayExecutionStatus
from medilink_ai.gateway.safety import AISafetyService

from .conftest import make_orchestrator
from .fakes import FakeExecutor


def test_safety_classifier_failure_blocks(authorized_principal, knowledge_request):
    class BrokenSafety:
        def classify(self, *args, **kwargs):
            raise RuntimeError("safety unavailable")
    executor = FakeExecutor()
    orchestrator = make_orchestrator(executor=executor)
    orchestrator.safety_service = BrokenSafety()
    result = asyncio.run(orchestrator.execute(principal=authorized_principal, request=knowledge_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert result.reason_codes == ("SAFETY_CLASSIFICATION_FAILED",)
    assert executor.calls == []
