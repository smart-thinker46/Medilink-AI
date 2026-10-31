from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PHILevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    RESTRICTED = "RESTRICTED"


class PHIType(str, Enum):
    PATIENT_NAME = "PATIENT_NAME"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    ADDRESS = "ADDRESS"
    NATIONAL_ID = "NATIONAL_ID"
    PASSPORT = "PASSPORT"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    PATIENT_ID = "PATIENT_ID"
    MEDICAL_RECORD_NUMBER = "MEDICAL_RECORD_NUMBER"
    ENCOUNTER_ID = "ENCOUNTER_ID"
    DIAGNOSIS = "DIAGNOSIS"
    CLINICAL_NOTE = "CLINICAL_NOTE"
    LAB_RESULT = "LAB_RESULT"
    RADIOLOGY_REPORT = "RADIOLOGY_REPORT"
    MEDICATION = "MEDICATION"
    ALLERGY = "ALLERGY"
    INSURANCE_INFORMATION = "INSURANCE_INFORMATION"
    BILLING_INFORMATION = "BILLING_INFORMATION"
    STAFF_INFORMATION = "STAFF_INFORMATION"


@dataclass(frozen=True)
class PHIMatch:
    phi_type: PHIType
    level: PHILevel
    start: int
    end: int
    value: str = ""


@dataclass(frozen=True)
class PHIInspectionResult:
    matches: tuple[PHIMatch, ...] = ()

    @property
    def contains_phi(self) -> bool:
        return bool(self.matches)

    @property
    def highest_level(self) -> PHILevel:
        order = {level: index for index, level in enumerate(PHILevel)}
        return max(self.matches, key=lambda match: order[match.level]).level if self.matches else PHILevel.NONE


@dataclass(frozen=True)
class ProtectedText:
    original_length: int
    protected_text: str
    inspection: PHIInspectionResult
    minimized: bool = False


@dataclass(frozen=True)
class PHIProcessingDecision:
    allowed: bool
    level: PHILevel
    reason_code: str = "NONE"
    minimized: bool = False
    inspection: PHIInspectionResult | None = None


@dataclass(frozen=True)
class AIContextField:
    name: str
    value: object
    classification: PHILevel
    required: bool = False


@dataclass(frozen=True)
class ProtectedAIContext:
    fields: tuple[AIContextField, ...] = field(default_factory=tuple)

    @property
    def allowed_fields(self) -> tuple[AIContextField, ...]:
        return tuple(item for item in self.fields if item.value is not None)


@dataclass(frozen=True)
class PHIAuditMetadata:
    request_id: str
    capability: str
    contains_phi: bool
    phi_level: PHILevel
    minimized: bool
    blocked: bool
    reason_code: str
