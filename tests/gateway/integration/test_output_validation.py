import asyncio

from medilink_ai.gateway.output import AIOutputValidationService
from medilink_ai.gateway.orchestration import GatewayExecutionStatus

from .conftest import make_orchestrator
from .fakes import FakeExecutor


def test_invalid_model_output_is_blocked(authorized_principal, knowledge_request):
    executor = FakeExecutor(result={"answer": "bad", "status": "ANSWERED", "unexpected": True})
    result = asyncio.run(make_orchestrator(executor=executor, output_validator=AIOutputValidationService()).execute(principal=authorized_principal, request=knowledge_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert "OUTPUT_SCHEMA_INVALID" in result.reason_codes


def test_unsafe_model_output_is_blocked(authorized_principal, knowledge_request):
    executor = FakeExecutor(result={"answer": "Approve the patient's discharge.", "status": "ANSWERED"})
    result = asyncio.run(make_orchestrator(executor=executor, output_validator=AIOutputValidationService()).execute(principal=authorized_principal, request=knowledge_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert "OUTPUT_ATTEMPTS_DISCHARGE_APPROVAL" in result.reason_codes
