from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ContextAccessStatus(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"


@dataclass(frozen=True)
class ContextAccessDecision:
    """Result of an authoritative patient/encounter access check."""

    status: ContextAccessStatus
    reason_code: str | None = None


@dataclass(frozen=True)
class PatientContextRecord:
    """Minimal patient ownership data returned by the HMIS context service."""

    patient_id: str
    organization_id: str
    facility_id: str


@dataclass(frozen=True)
class EncounterContextRecord:
    """Minimal encounter ownership and relationship data."""

    encounter_id: str
    patient_id: str
    organization_id: str
    facility_id: str
    # Optional because older HMIS APIs may not expose encounter department.
    department_id: str | None = None


@dataclass(frozen=True)
class ValidatedRequestContext:
    """Trusted context produced only after all ownership/access checks pass."""

    organization_id: str
    facility_id: str
    department_id: str | None
    patient: PatientContextRecord | None
    encounter: EncounterContextRecord | None
    purpose: str
    patient_access: ContextAccessDecision | None = None
    encounter_access: ContextAccessDecision | None = None
    validated_at: datetime | None = None

    @property
    def patient_id(self) -> str | None:
        return self.patient.patient_id if self.patient else None

    @property
    def encounter_id(self) -> str | None:
        return self.encounter.encounter_id if self.encounter else None
