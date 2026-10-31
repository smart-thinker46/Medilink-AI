from __future__ import annotations

from .models import AIContextField, PHIInspectionResult, PHIType, ProtectedAIContext, ProtectedText


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
