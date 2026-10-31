from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AICapability(str, Enum):
    KNOWLEDGE_ASK = "knowledge.ask"
    PATIENT_SUMMARY = "patient.summary"
    DOCUMENTATION_DRAFT = "documentation.draft"
    OPERATIONAL_INSIGHTS = "operational.insights"


class AIRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GatewayDecisionStatus(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject_id: str
    organization_id: str
    facility_ids: frozenset[str] = frozenset()
    department_ids: frozenset[str] = frozenset()
    roles: frozenset[str] = frozenset()
    permissions: frozenset[str] = frozenset()
    classification_level: str = "INTERNAL"


@dataclass(frozen=True)
class GatewayDecision:
    status: GatewayDecisionStatus
    reason_codes: tuple[str, ...] = ()
    risk_level: AIRiskLevel = AIRiskLevel.LOW


@dataclass(frozen=True)
class GatewayExecutionContext:
    principal: AuthenticatedPrincipal
    capability: AICapability
    facility_id: str
    department_id: str | None = None
    patient_id: str | None = None
    encounter_id: str | None = None
