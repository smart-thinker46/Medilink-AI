import asyncio

from medilink_ai.gateway import AICapability, AuthenticatedPrincipal, GatewayRequest
from medilink_ai.gateway.routing import ModelRegistry, ModelRouter, ProtectedModelInput, RoutedAIExecutor


class FakeInference:
    def __init__(self):
        self.model_name = None
        self.arguments = None

    async def generate(self, **kwargs):
        self.arguments = kwargs
        self.model_name = kwargs["model_name"]
        return "generated"


def test_routed_executor_passes_selected_model_to_provider():
    inference = FakeInference()
    executor = RoutedAIExecutor(router=ModelRouter(ModelRegistry()), inference_executor=inference)
    result = asyncio.run(executor.execute(
        request=GatewayRequest(capability=AICapability.KNOWLEDGE_ASK, module="clinical", facility_id="facility-001", query="Explain policy"),
        principal=AuthenticatedPrincipal("u", "o", frozenset({"facility-001"})), validated_context={},
        protected_request=ProtectedModelInput(
            capability="knowledge.ask", purpose="policy question",
            query="Explain policy", patient_reference=None, encounter_reference=None,
            patient_data={}, encounter_data={}, human_review_required=False,
        ),
    ))
    assert result == "generated"
    assert inference.model_name == "qwen2.5:0.5b"
    assert set(inference.arguments) == {"model_name", "request_id", "model_input"}
    assert inference.arguments["model_input"].query == "Explain policy"



def test_routed_executor_rejects_unprotected_input():
    import pytest
    from medilink_ai.gateway.routing import UnprotectedModelInputError

    inference = FakeInference()
    executor = RoutedAIExecutor(router=ModelRouter(ModelRegistry()), inference_executor=inference)
    with pytest.raises(UnprotectedModelInputError):
        asyncio.run(executor.execute(
            request=GatewayRequest(capability=AICapability.KNOWLEDGE_ASK, module="clinical", facility_id="facility-001", query="Explain policy"),
            principal=AuthenticatedPrincipal("u", "o", frozenset({"facility-001"})),
            validated_context={},
            protected_request={"query": "raw text"},
        ))
