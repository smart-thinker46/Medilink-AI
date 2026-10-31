from __future__ import annotations

from .errors import ModelCapabilityError, ModelNotFoundError, ModelPolicyError
from .models import ModelAvailability, ModelRoutingDecision, ModelRoutingRequest, RoutingDecisionStatus
from .policy import get_capability_routing_policy
from .registry import ModelRegistry


class ModelRouter:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def route(self, request: ModelRoutingRequest) -> ModelRoutingDecision:
        policy = get_capability_routing_policy(request.capability)
        if policy is None:
            return ModelRoutingDecision(RoutingDecisionStatus.BLOCKED, reason_code="CAPABILITY_ROUTING_POLICY_MISSING")
        if request.minimum_output_tokens < policy.minimum_output_tokens:
            requested_minimum = policy.minimum_output_tokens
        else:
            requested_minimum = request.minimum_output_tokens
        requires_json = request.requires_json or policy.requires_json

        if request.requested_model_id:
            model = self.registry.get(request.requested_model_id)
            if model is None:
                raise ModelNotFoundError("Requested model is not registered.")
            self._validate_model(model, policy, requested_minimum, requires_json, request)
            if model.availability not in {ModelAvailability.AVAILABLE, ModelAvailability.DEGRADED}:
                return ModelRoutingDecision(RoutingDecisionStatus.BLOCKED, reason_code="REQUESTED_MODEL_UNAVAILABLE")
            return ModelRoutingDecision(RoutingDecisionStatus.ROUTED, model, "EXPLICIT_APPROVED_MODEL")

        candidates = []
        for model_id in policy.preferred_model_ids:
            model = self.registry.get(model_id)
            if model is None:
                continue
            try:
                self._validate_model(model, policy, requested_minimum, requires_json, request)
            except (ModelCapabilityError, ModelPolicyError):
                continue
            if model.availability in {ModelAvailability.AVAILABLE, ModelAvailability.DEGRADED}:
                candidates.append(model)
        if not candidates:
            return ModelRoutingDecision(RoutingDecisionStatus.BLOCKED, reason_code="NO_APPROVED_MODEL_AVAILABLE")
        model = candidates[0]
        fallback = policy.preferred_model_ids.index(model.model_id) > 0 or model.availability == ModelAvailability.DEGRADED
        return ModelRoutingDecision(RoutingDecisionStatus.FALLBACK if fallback else RoutingDecisionStatus.ROUTED, model, "APPROVED_FALLBACK" if fallback else "APPROVED_MODEL", fallback)

    @staticmethod
    def _validate_model(model, policy, minimum_output_tokens, requires_json, request):
        if policy.model_capability not in model.capabilities:
            raise ModelCapabilityError("Model is not approved for this capability.")
        if minimum_output_tokens > model.max_output_tokens:
            raise ModelPolicyError("Model output capacity is below the policy minimum.")
        if requires_json and not model.supports_json:
            raise ModelPolicyError("Model does not support the required structured output.")
        if request.requires_tools and not model.supports_tools:
            raise ModelPolicyError("Model does not support required tools.")
        if request.requires_vision and not model.supports_vision:
            raise ModelPolicyError("Model does not support required vision input.")
