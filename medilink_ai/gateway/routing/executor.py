from __future__ import annotations

from typing import Any, Protocol

from ..models import AuthenticatedPrincipal
from ..schemas import GatewayRequest
from .errors import NoModelAvailableError
from .models import ModelRoutingRequest
from .router import ModelRouter


class InferenceExecutor(Protocol):
    async def generate(self, *, model_name: str, request: GatewayRequest, principal: AuthenticatedPrincipal, validated_context: Any, protected_request: Any) -> Any:
        ...


class RoutedAIExecutor:
    def __init__(self, *, router: ModelRouter, inference_executor: InferenceExecutor):
        self.router = router
        self.inference_executor = inference_executor

    async def execute(self, *, request: GatewayRequest, principal: AuthenticatedPrincipal, validated_context: Any, protected_request: Any, routing_request: ModelRoutingRequest | None = None) -> Any:
        model_request = routing_request or ModelRoutingRequest(capability=request.capability)
        decision = self.router.route(model_request)
        if decision.model is None:
            raise NoModelAvailableError(decision.reason_code)
        return await self.inference_executor.generate(model_name=decision.model.model_name, request=request, principal=principal, validated_context=validated_context, protected_request=protected_request)
