import asyncio

from medilink_ai.gateway import AICapability, AuthenticatedPrincipal, GatewayRequest
from medilink_ai.gateway.routing import ModelRegistry, ModelRouter, RoutedAIExecutor


class FakeInference:
    def __init__(self):
        self.model_name = None

    async def generate(self, **kwargs):
        self.model_name = kwargs["model_name"]
        return "generated"


def test_routed_executor_passes_selected_model_to_provider():
    inference = FakeInference()
    executor = RoutedAIExecutor(router=ModelRouter(ModelRegistry()), inference_executor=inference)
    result = asyncio.run(executor.execute(
        request=GatewayRequest(capability=AICapability.KNOWLEDGE_ASK, module="clinical", facility_id="facility-001", query="Explain policy"),
        principal=AuthenticatedPrincipal("u", "o", frozenset({"facility-001"})), validated_context={}, protected_request={},
    ))
    assert result == "generated"
    assert inference.model_name == "qwen2.5:0.5b"
