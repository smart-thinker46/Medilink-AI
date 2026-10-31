from __future__ import annotations

from ..models import AICapability, AIRiskLevel
from .classifier import SafetyActionClassifier
from .models import AIActionType, AISafetyDecision, SafetyClassification
from .policy import default_decision_for_risk, is_critical_action
from .rules import SAFETY_RULES, SafetyRule


class AISafetyService:
    """Classifies requested intent before any model inference is attempted."""

    def __init__(self, classifier: SafetyActionClassifier | None = None):
        self.classifier = classifier or SafetyActionClassifier()

    @staticmethod
    def _find_rule(capability: AICapability, action_type: AIActionType) -> SafetyRule | None:
        return next((rule for rule in SAFETY_RULES if rule.action_type == action_type and (rule.capability is None or rule.capability == capability)), None)

    def classify(self, capability: AICapability, query: str) -> SafetyClassification:
        try:
            action = self.classifier.classify(query)
        except Exception as exc:
            # A classifier failure must never turn into an allowed request.
            return SafetyClassification(AIRiskLevel.HIGH, AIActionType.ANALYZE, AISafetyDecision.REVIEW_REQUIRED, "SAFETY_CLASSIFICATION_UNAVAILABLE", requires_human_review=True)

        if is_critical_action(action) and any(term in query.lower() for term in ("transfusion", "blood release", "blood bank")):
            return SafetyClassification(AIRiskLevel.CRITICAL, action, AISafetyDecision.ESCALATE, "SPECIALIZED_BLOOD_WORKFLOW_REQUIRED", requires_specialized_workflow=True)
        if is_critical_action(action):
            return SafetyClassification(AIRiskLevel.CRITICAL, action, AISafetyDecision.DENY, "CRITICAL_ACTION_NOT_PERMITTED", requires_specialized_workflow=True)

        rule = self._find_rule(capability, action)
        if rule:
            return SafetyClassification(rule.risk_level, action, rule.decision, rule.reason_code, rule.rule_id, rule.requires_human_review, rule.requires_specialized_workflow)

        # Unknown or capability/action combinations are high-risk and require review.
        risk = AIRiskLevel.HIGH
        return SafetyClassification(risk, action, default_decision_for_risk(risk), "UNCLASSIFIED_ACTION_REQUIRES_REVIEW", requires_human_review=True)
