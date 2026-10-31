from __future__ import annotations

from typing import Protocol

from ..models import AuthenticatedPrincipal
from .models import (
    ContextAccessDecision,
    EncounterContextRecord,
    PatientContextRecord,
)


class HMISContextProvider(Protocol):
    """Read-only interface to authoritative Medilink context services."""

    async def get_patient(self, patient_id: str) -> PatientContextRecord | None:
        ...

    async def get_encounter(self, encounter_id: str) -> EncounterContextRecord | None:
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
