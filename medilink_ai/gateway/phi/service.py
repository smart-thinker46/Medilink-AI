from __future__ import annotations

from ..models import AICapability
from .detector import PHIDetector
from .exceptions import PHIDetectionError, PHIMinimizationError, PHIPolicyViolation
from .inspector import PHIInspector
from .minimizer import PHIMinimizer
from .models import AIContextField, PHILevel, PHIProcessingDecision, PHIType, ProtectedAIContext, ProtectedText
from .policy import get_phi_policy


class PHIProtectionService:
    LEVEL_ORDER = {level: index for index, level in enumerate(PHILevel)}
    DIRECT_IDENTIFIER_TYPES = frozenset({
        PHIType.PATIENT_NAME, PHIType.PHONE, PHIType.EMAIL, PHIType.ADDRESS,
        PHIType.NATIONAL_ID, PHIType.PASSPORT, PHIType.DATE_OF_BIRTH,
        PHIType.PATIENT_ID, PHIType.MEDICAL_RECORD_NUMBER, PHIType.ENCOUNTER_ID,
    })

    def __init__(self, detector: PHIDetector | None = None, minimizer: PHIMinimizer | None = None, inspector: PHIInspector | None = None):
        self.detector = detector or PHIDetector()
        self.minimizer = minimizer or PHIMinimizer()
        self.inspector = inspector or PHIInspector(self.detector)

    def evaluate(self, capability: AICapability, text: str) -> PHIProcessingDecision:
        try:
            inspection = self.inspector.inspect(text)
        except Exception as exc:
            raise PHIDetectionError("PHI inspection could not be completed safely.") from exc
        level = inspection.highest_level
        policy = get_phi_policy(capability)
        contains_direct_identifier = any(match.phi_type in self.DIRECT_IDENTIFIER_TYPES for match in inspection.matches)
        if self.LEVEL_ORDER[level] <= self.LEVEL_ORDER[policy.maximum_level]:
            if contains_direct_identifier and not policy.allow_direct_identifiers:
                replaceable = all(match.phi_type in self.minimizer.REPLACEMENTS for match in inspection.matches)
                if replaceable and level != PHILevel.RESTRICTED:
                    return PHIProcessingDecision(True, level, "DIRECT_IDENTIFIERS_MINIMIZATION_REQUIRED", True, inspection)
                return PHIProcessingDecision(False, level, "DIRECT_IDENTIFIERS_NOT_ALLOWED", False, inspection)
            return PHIProcessingDecision(True, level, "NONE", False, inspection)
        # Direct identifiers can be safely removed before model processing;
        # restricted identifiers must block rather than rely on redaction.
        replaceable = all(match.phi_type in self.minimizer.REPLACEMENTS for match in inspection.matches)
        if policy.require_minimization and replaceable and level != PHILevel.RESTRICTED:
            return PHIProcessingDecision(True, level, "PHI_MINIMIZATION_REQUIRED", True, inspection)
        return PHIProcessingDecision(False, level, "PHI_LEVEL_EXCEEDS_CAPABILITY_POLICY", False, inspection)

    def protect_text(self, capability: AICapability, text: str) -> ProtectedText:
        decision = self.evaluate(capability, text)
        if not decision.allowed:
            raise PHIPolicyViolation("The requested AI context exceeds the capability PHI policy.")
        try:
            return self.minimizer.minimize(text, decision.inspection or self.inspector.inspect(text)) if decision.minimized else ProtectedText(len(text), text, decision.inspection or self.inspector.inspect(text), False)
        except Exception as exc:
            raise PHIMinimizationError("Required PHI minimization could not be completed safely.") from exc

    def protect_fields(self, capability: AICapability, fields: tuple[AIContextField, ...], allowed_names: frozenset[str]) -> ProtectedAIContext:
        policy = get_phi_policy(capability)
        requested = [field for field in fields if field.name in allowed_names and field.value is not None]
        if not policy.allow_patient_context and any(field.name.startswith("patient.") for field in requested):
            raise PHIPolicyViolation("Patient context is not permitted for this AI capability.")
        direct_names = ("name", "phone", "email", "address", "national_id", "passport", "date_of_birth", "patient_id", "mrn", "encounter_id")
        clinical_names = ("diagnosis", "clinical", "note", "lab", "radiology", "medication", "allergy", "vital")
        filtered = []
        for field in requested:
            lowered = field.name.lower()
            if not policy.allow_direct_identifiers and any(token in lowered for token in direct_names):
                if field.required:
                    raise PHIPolicyViolation("A required direct identifier is not permitted for this AI capability.")
                continue
            if not policy.allow_clinical_content and any(token in lowered for token in clinical_names):
                if field.required:
                    raise PHIPolicyViolation("Required clinical content is not permitted for this AI capability.")
                continue
            if self.LEVEL_ORDER[field.classification] > self.LEVEL_ORDER[policy.maximum_level]:
                if field.required:
                    raise PHIPolicyViolation("A required field exceeds the capability PHI policy.")
                continue
            filtered.append(field)
        return ProtectedAIContext(tuple(filtered))
