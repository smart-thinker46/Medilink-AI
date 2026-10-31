from __future__ import annotations

from .models import AIContextField, PHIInspectionResult, PHIType, ProtectedAIContext, ProtectedText
from .exceptions import PHIValidationError
from typing import Any, Mapping

SCALAR_TYPES = (str, int, float, bool)


def minimize_projection(data: Mapping[str, Any], allowed_fields: frozenset[str], maximum_field_characters: int = 4000) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise PHIValidationError("HMIS data provider returned an invalid projection.")
    if set(data) - set(allowed_fields):
        raise PHIValidationError("HMIS provider returned fields outside the approved PHI policy.")
    result: dict[str, Any] = {}
    for name, value in data.items():
        values = value if isinstance(value, (list, tuple)) else (value,)
        if not isinstance(name, str) or name not in allowed_fields:
            raise PHIValidationError("HMIS provider returned an unauthorized field.")
        if value is not None and not isinstance(value, (list, tuple)) and not isinstance(value, SCALAR_TYPES):
            raise PHIValidationError("HMIS projection contains an unsupported nested value.")
        if isinstance(value, (list, tuple)) and any(item is not None and not isinstance(item, SCALAR_TYPES) for item in value):
            raise PHIValidationError("HMIS projection contains an unsupported nested value.")
        if any(isinstance(item, str) and len(item) > maximum_field_characters for item in values):
            raise PHIValidationError("HMIS projection contains an oversized field.")
        result[name] = list(value) if isinstance(value, tuple) else value
    return result


class PHIMinimizer:
    REPLACEMENTS = {
        PHIType.PHONE: "[PHONE_REDACTED]",
        PHIType.EMAIL: "[EMAIL_REDACTED]",
        PHIType.NATIONAL_ID: "[NATIONAL_ID_REDACTED]",
        PHIType.PASSPORT: "[PASSPORT_REDACTED]",
        PHIType.DATE_OF_BIRTH: "[DATE_OF_BIRTH_REDACTED]",
        PHIType.MEDICAL_RECORD_NUMBER: "[MRN_REDACTED]",
        PHIType.PATIENT_ID: "[PATIENT_ID_REDACTED]",
        PHIType.ENCOUNTER_ID: "[ENCOUNTER_ID_REDACTED]",
    }

    def minimize(self, text: str, inspection: PHIInspectionResult) -> ProtectedText:
        protected = text
        for match in sorted(inspection.matches, key=lambda item: item.start, reverse=True):
            protected = protected[:match.start] + self.REPLACEMENTS.get(match.phi_type, "[PHI_REDACTED]") + protected[match.end:]
        return ProtectedText(len(text), protected, inspection, bool(inspection.matches))

    def minimize_fields(self, fields: tuple[AIContextField, ...], allowed_names: frozenset[str]) -> ProtectedAIContext:
        return ProtectedAIContext(tuple(field for field in fields if field.name in allowed_names and field.value is not None))
