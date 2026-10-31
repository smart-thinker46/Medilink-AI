from __future__ import annotations

from dataclasses import dataclass

from .models import AICapability


@dataclass(frozen=True)
class CapabilityPolicy:
    capability: AICapability
    allowed_modules: frozenset[str]
    required_permissions: frozenset[str]
    requires_patient: bool = False
    requires_encounter: bool = False
    description: str = ""


CAPABILITY_POLICIES = {
    AICapability.KNOWLEDGE_ASK: CapabilityPolicy(
        AICapability.KNOWLEDGE_ASK,
        frozenset({"clinical", "pharmacy", "laboratory", "nursing", "billing", "administration"}),
        frozenset({"ai:knowledge:ask", "ai:capability:knowledge.ask"}),
        description="Ask questions about authorized hospital knowledge.",
    ),
    AICapability.PATIENT_SUMMARY: CapabilityPolicy(
        AICapability.PATIENT_SUMMARY, frozenset({"clinical"}),
        frozenset({"ai:patient_summary", "ai:capability:patient.summary"}), requires_patient=True,
        description="Summarize an authorized patient record.",
    ),
    AICapability.DOCUMENTATION_DRAFT: CapabilityPolicy(
        AICapability.DOCUMENTATION_DRAFT, frozenset({"clinical"}),
        frozenset({"ai:documentation:draft", "ai:capability:documentation.draft"}), requires_patient=True,
        description="Draft documentation for human review.",
    ),
    AICapability.OPERATIONAL_INSIGHTS: CapabilityPolicy(
        AICapability.OPERATIONAL_INSIGHTS, frozenset({"administration", "billing", "nursing"}),
        frozenset({"ai:operational:insights", "ai:capability:operational.insights"}),
        description="Analyze authorized operational information.",
    ),
}


def get_capability_policy(capability: AICapability) -> CapabilityPolicy:
    try:
        return CAPABILITY_POLICIES[capability]
    except KeyError as exc:
        raise ValueError(f"Unsupported AI capability: {capability}") from exc
