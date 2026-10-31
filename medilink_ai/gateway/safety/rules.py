from __future__ import annotations

from dataclasses import dataclass

from ..models import AICapability, AIRiskLevel
from .models import AIActionType, AISafetyDecision


@dataclass(frozen=True)
class SafetyRule:
    rule_id: str
    capability: AICapability | None
    action_type: AIActionType
    risk_level: AIRiskLevel
    decision: AISafetyDecision
    reason_code: str
    requires_human_review: bool = False
    requires_specialized_workflow: bool = False


SAFETY_RULES: tuple[SafetyRule, ...] = (
    SafetyRule("SAFE-001", AICapability.KNOWLEDGE_ASK, AIActionType.EXPLAIN, AIRiskLevel.LOW, AISafetyDecision.ALLOW, "GENERAL_KNOWLEDGE_ASSISTANCE"),
    SafetyRule("SAFE-002", AICapability.KNOWLEDGE_ASK, AIActionType.RETRIEVE, AIRiskLevel.LOW, AISafetyDecision.ALLOW, "AUTHORIZED_KNOWLEDGE_RETRIEVAL"),
    SafetyRule("SAFE-003", AICapability.KNOWLEDGE_ASK, AIActionType.CLASSIFY, AIRiskLevel.LOW, AISafetyDecision.ALLOW, "KNOWLEDGE_CLASSIFICATION"),
    SafetyRule("SAFE-004", AICapability.PATIENT_SUMMARY, AIActionType.SUMMARIZE, AIRiskLevel.MODERATE, AISafetyDecision.REVIEW_REQUIRED, "PATIENT_SUMMARY_REQUIRES_CLINICIAN_REVIEW", True),
    SafetyRule("SAFE-005", AICapability.DOCUMENTATION_DRAFT, AIActionType.DRAFT, AIRiskLevel.MODERATE, AISafetyDecision.REVIEW_REQUIRED, "CLINICAL_DRAFT_REQUIRES_HUMAN_REVIEW", True),
    SafetyRule("SAFE-006", AICapability.OPERATIONAL_INSIGHTS, AIActionType.ANALYZE, AIRiskLevel.HIGH, AISafetyDecision.REVIEW_REQUIRED, "OPERATIONAL_ANALYSIS_REQUIRES_REVIEW", True),
    SafetyRule("SAFE-007", None, AIActionType.RECOMMEND, AIRiskLevel.HIGH, AISafetyDecision.REVIEW_REQUIRED, "RECOMMENDATION_REQUIRES_QUALIFIED_REVIEW", True),
)
