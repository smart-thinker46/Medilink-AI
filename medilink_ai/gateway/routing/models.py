from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from typing import Any, Mapping

from ..models import AICapability


class ModelCapability(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    PATIENT_SUMMARY = "PATIENT_SUMMARY"
    DOCUMENTATION = "DOCUMENTATION"
    CLASSIFICATION = "CLASSIFICATION"
    GENERAL = "GENERAL"


class ModelAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DEGRADED = "DEGRADED"
    DISABLED = "DISABLED"


class RoutingDecisionStatus(str, Enum):
    ROUTED = "ROUTED"
    FALLBACK = "FALLBACK"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ModelDefinition:
    model_id: str
    provider: str
    model_name: str
    capabilities: frozenset[ModelCapability]
    priority: int = 100
    max_input_tokens: int = 4096
    max_output_tokens: int = 512
    temperature: float = 0.1
    availability: ModelAvailability = ModelAvailability.AVAILABLE
    supports_json: bool = False
    supports_tools: bool = False
    supports_vision: bool = False
    evaluation_version: str | None = None
    evaluation_passed: bool = False
    approved_for_production: bool = False


@dataclass(frozen=True)
class ModelRoutingRequest:
    capability: AICapability
    minimum_output_tokens: int = 1
    requires_json: bool = False
    requires_tools: bool = False
    requires_vision: bool = False
    requested_model_id: str | None = None
    # Kept as an internal routing hint, never sourced from GatewayRequest.
    model_capability: ModelCapability | None = None


@dataclass(frozen=True)
class ModelRoutingDecision:
    status: RoutingDecisionStatus
    model: ModelDefinition | None = None
    reason_code: str = "NONE"
    fallback_used: bool = False


@dataclass(frozen=True)
class ProtectedModelInput:
    capability: str
    purpose: str
    query: str
    patient_reference: str | None
    encounter_reference: str | None
    patient_data: Mapping[str, Any]
    encounter_data: Mapping[str, Any]
    human_review_required: bool

    @classmethod
    def from_protected_context(cls, context):
        from ..phi.models import ProtectedAIContext
        if not isinstance(context, ProtectedAIContext):
            raise TypeError("A validated ProtectedAIContext is required.")
        return cls(context.capability, context.purpose, context.query, context.patient_reference,
                   context.encounter_reference, dict(context.patient_data), dict(context.encounter_data),
                   context.human_review_required)
