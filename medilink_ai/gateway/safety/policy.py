from __future__ import annotations

from .models import AIActionType, AISafetyDecision
from ..models import AIRiskLevel


DEFAULT_RISK_DECISIONS = {
    AIRiskLevel.LOW: AISafetyDecision.ALLOW,
    AIRiskLevel.MODERATE: AISafetyDecision.REVIEW_REQUIRED,
    AIRiskLevel.HIGH: AISafetyDecision.REVIEW_REQUIRED,
    AIRiskLevel.CRITICAL: AISafetyDecision.DENY,
}

CLINICAL_CRITICAL_ACTIONS = frozenset({
    AIActionType.AUTHORIZE,
    AIActionType.APPROVE,
    AIActionType.MODIFY,
    AIActionType.EXECUTE,
})


def default_decision_for_risk(risk_level: AIRiskLevel) -> AISafetyDecision:
    return DEFAULT_RISK_DECISIONS[risk_level]


def is_critical_action(action_type: AIActionType) -> bool:
    return action_type in CLINICAL_CRITICAL_ACTIONS
