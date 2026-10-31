from __future__ import annotations

from .capability_registry import get_capability_policy
from .models import (
    AuthenticatedPrincipal,
    AIRiskLevel,
    GatewayDecision,
    GatewayDecisionStatus,
)
from .schemas import GatewayRequest


def authorize_gateway_request(principal: AuthenticatedPrincipal, request: GatewayRequest, *, patient_access_verified: bool = False, encounter_access_verified: bool = False) -> GatewayDecision:
    reasons: list[str] = []
    if not principal.subject_id:
        reasons.append("MISSING_AUTHENTICATED_IDENTITY")
    if not principal.organization_id:
        reasons.append("MISSING_ORGANIZATION_CONTEXT")
    policy = get_capability_policy(request.capability)
    if request.module.lower() not in policy.allowed_modules:
        reasons.append("MODULE_ACCESS_DENIED")
    if request.facility_id not in principal.facility_ids:
        reasons.append("FACILITY_ACCESS_DENIED")
    if request.department_id and principal.department_ids and request.department_id not in principal.department_ids:
        reasons.append("DEPARTMENT_ACCESS_DENIED")
    if "ai:use" not in principal.permissions:
        reasons.append("AI_ACCESS_NOT_GRANTED")
    if not (policy.required_permissions & principal.permissions):
        reasons.append("CAPABILITY_ACCESS_NOT_GRANTED")
    if policy.requires_patient and not request.patient_id:
        reasons.append("PATIENT_CONTEXT_REQUIRED")
    if policy.requires_encounter and not request.encounter_id:
        reasons.append("ENCOUNTER_CONTEXT_REQUIRED")
    if request.patient_id and not patient_access_verified:
        reasons.append("PATIENT_ACCESS_NOT_VERIFIED")
    if request.encounter_id and not encounter_access_verified:
        reasons.append("ENCOUNTER_ACCESS_NOT_VERIFIED")
    if reasons:
        return GatewayDecision(GatewayDecisionStatus.DENIED, tuple(reasons), AIRiskLevel.HIGH if request.patient_id else AIRiskLevel.MODERATE)
    return GatewayDecision(GatewayDecisionStatus.ALLOWED, (), AIRiskLevel.HIGH if request.patient_id else AIRiskLevel.LOW)
