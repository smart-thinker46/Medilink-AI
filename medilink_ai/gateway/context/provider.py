from __future__ import annotations

from typing import Protocol

from ..models import AuthenticatedPrincipal
from .models import (
    ContextAccessDecision,
    DepartmentContextRecord,
    EncounterContextRecord,
    PatientContextRecord,
)


class HMISContextProvider(Protocol):
    """Read-only interface to authoritative Medilink context services."""

    async def get_patient(self, patient_id: str, organization_id: str | None = None) -> PatientContextRecord | None:
        ...

    async def get_encounter(self, encounter_id: str, organization_id: str | None = None) -> EncounterContextRecord | None:
        ...

    async def get_department(self, department_id: str, organization_id: str, facility_id: str) -> DepartmentContextRecord | None:
        ...


class PatientEncounterAccessAuthorizer(Protocol):
    """User-specific access checks; ownership alone never grants access."""

    async def authorize_patient(
        self,
        principal: AuthenticatedPrincipal,
        patient: PatientContextRecord,
        purpose: str,
    ) -> ContextAccessDecision:
        ...

    async def authorize_encounter(
        self,
        principal: AuthenticatedPrincipal,
        encounter: EncounterContextRecord,
        purpose: str,
    ) -> ContextAccessDecision:
        ...


PatientAccessAuthorizer = PatientEncounterAccessAuthorizer
