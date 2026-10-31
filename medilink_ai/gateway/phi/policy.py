from __future__ import annotations

from dataclasses import dataclass

from ..models import AICapability
from .models import PHILevel


@dataclass(frozen=True)
class PHIPolicy:
    capability: AICapability
    maximum_level: PHILevel
    allow_patient_context: bool
    allow_direct_identifiers: bool
    allow_clinical_content: bool
    require_minimization: bool
    require_human_review_for_restricted: bool


PHI_POLICIES: dict[AICapability, PHIPolicy] = {
    AICapability.KNOWLEDGE_ASK: PHIPolicy(AICapability.KNOWLEDGE_ASK, PHILevel.LOW, False, False, False, True, True),
    AICapability.PATIENT_SUMMARY: PHIPolicy(AICapability.PATIENT_SUMMARY, PHILevel.HIGH, True, False, True, True, True),
    AICapability.DOCUMENTATION_DRAFT: PHIPolicy(AICapability.DOCUMENTATION_DRAFT, PHILevel.HIGH, True, False, True, True, True),
    AICapability.OPERATIONAL_INSIGHTS: PHIPolicy(AICapability.OPERATIONAL_INSIGHTS, PHILevel.MODERATE, False, False, False, True, True),
}


def get_phi_policy(capability: AICapability) -> PHIPolicy:
    try:
        return PHI_POLICIES[capability]
    except KeyError as exc:
        raise ValueError(f"No PHI policy configured for capability: {capability}") from exc
