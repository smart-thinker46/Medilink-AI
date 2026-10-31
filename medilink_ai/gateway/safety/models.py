from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..models import AIRiskLevel


class AISafetyDecision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DENY = "DENY"
    ESCALATE = "ESCALATE"


class AIActionType(str, Enum):
    EXPLAIN = "EXPLAIN"
    SUMMARIZE = "SUMMARIZE"
    CLASSIFY = "CLASSIFY"
    RETRIEVE = "RETRIEVE"
    DRAFT = "DRAFT"
    ANALYZE = "ANALYZE"
    RECOMMEND = "RECOMMEND"
    AUTHORIZE = "AUTHORIZE"
    APPROVE = "APPROVE"
    MODIFY = "MODIFY"
    EXECUTE = "EXECUTE"


@dataclass(frozen=True)
class SafetyClassification:
    risk_level: AIRiskLevel
    action_type: AIActionType
    decision: AISafetyDecision = AISafetyDecision.REVIEW_REQUIRED
    reason_code: str = "UNCLASSIFIED_ACTION_REQUIRES_REVIEW"
    rule_id: str | None = None
    requires_human_review: bool = False
    requires_specialized_workflow: bool = False
