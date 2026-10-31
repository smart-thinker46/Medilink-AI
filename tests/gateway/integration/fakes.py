from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from medilink_ai.gateway.context import (ContextAccessDecision, ContextAccessStatus, EncounterContextRecord, PatientContextRecord, ValidatedRequestContext)
from medilink_ai.gateway.phi import PHIHandlingDecision, ProtectedAIContext


@dataclass
class FakeContextService:
    result: Any = None
    error: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def validate(self, *, principal, request):
        self.calls.append({"principal": principal, "request": request})
        if self.error:
            raise self.error
        if self.result is not None:
            return self.result
        patient = PatientContextRecord(request.patient_id, principal.organization_id, request.facility_id) if request.patient_id else None
        encounter = EncounterContextRecord(request.encounter_id, request.patient_id, principal.organization_id, request.facility_id, request.department_id) if request.encounter_id else None
        allowed = ContextAccessDecision(ContextAccessStatus.ALLOWED)
        return ValidatedRequestContext(
            principal.organization_id, request.facility_id, request.department_id,
            patient, encounter, request.purpose or "test purpose",
            allowed if patient else None, allowed if encounter else None,
        )


@dataclass
class FakePHIService:
    result: Any = None
    error: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def protect(self, *, principal, request, validated_context):
        self.calls.append({"principal": principal, "request": request, "context": validated_context})
        if self.error:
            raise self.error
        if self.result is not None:
            return self.result
        return ProtectedAIContext(
            organization_id=validated_context.organization_id,
            facility_id=validated_context.facility_id,
            department_id=validated_context.department_id,
            capability=request.capability.value,
            purpose=(request.purpose or "").strip(),
            query=request.query or "",
            patient_reference="patient-ref" if validated_context.patient else None,
            encounter_reference="encounter-ref" if validated_context.encounter else None,
            patient_data={"age_band": "40-49"} if request.capability.value == "patient.summary" else {},
            encounter_data={"diagnoses": ["synthetic diagnosis"]} if request.capability.value == "patient.summary" else {},
            included_patient_fields=("age_band",) if request.capability.value == "patient.summary" else (),
            included_encounter_fields=("diagnoses",) if request.capability.value == "patient.summary" else (),
            decision=PHIHandlingDecision.ALLOWED,
            human_review_required=request.capability.value in {"patient.summary", "documentation.draft"},
        )


@dataclass
class FakeExecutor:
    result: Any = None
    error: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def execute(self, *, request, principal, validated_context, protected_request):
        self.calls.append({"request": request, "principal": principal, "context": validated_context, "protected": protected_request})
        if self.error:
            raise self.error
        return self.result if self.result is not None else {"answer": "ok"}


class FailingAuditService:
    def __init__(self):
        self.calls = 0

    def record(self, event):
        self.calls += 1
        raise RuntimeError("audit store unavailable")

