from __future__ import annotations

from dataclasses import dataclass

from ..models import AICapability
from .models import ModelCapability


@dataclass(frozen=True)
class CapabilityRoutingPolicy:
    capability: AICapability
    model_capability: ModelCapability
    preferred_model_ids: tuple[str, ...]
    minimum_output_tokens: int
    requires_json: bool = True
    requires_human_review: bool = False


CAPABILITY_ROUTING_POLICIES = {
    AICapability.KNOWLEDGE_ASK: CapabilityRoutingPolicy(AICapability.KNOWLEDGE_ASK, ModelCapability.KNOWLEDGE, ("knowledge-small", "knowledge-medium"), 200, True),
    AICapability.PATIENT_SUMMARY: CapabilityRoutingPolicy(AICapability.PATIENT_SUMMARY, ModelCapability.PATIENT_SUMMARY, ("patient-summary-model",), 500, True, True),
    AICapability.DOCUMENTATION_DRAFT: CapabilityRoutingPolicy(AICapability.DOCUMENTATION_DRAFT, ModelCapability.DOCUMENTATION, ("documentation-model",), 500, True, True),
    AICapability.OPERATIONAL_INSIGHTS: CapabilityRoutingPolicy(AICapability.OPERATIONAL_INSIGHTS, ModelCapability.GENERAL, ("operational-model",), 300, True, True),
}


def get_capability_routing_policy(capability: AICapability) -> CapabilityRoutingPolicy | None:
    return CAPABILITY_ROUTING_POLICIES.get(capability)
