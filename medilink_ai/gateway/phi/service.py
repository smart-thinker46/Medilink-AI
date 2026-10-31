from __future__ import annotations

from ..models import AICapability
from ..context.models import ContextAccessStatus, ValidatedRequestContext
from .detector import PHIDetector
from .exceptions import PHIDetectionError, PHIMinimizationError, PHIPolicyViolation
from .inspector import PHIInspector
from .minimizer import PHIMinimizer
from .models import AIContextField, PHILevel, PHIProcessingDecision, PHIType, ProtectedAIContext, ProtectedText
from .policy import get_phi_policy
from .policies import get_phi_policy as get_projection_policy
from .provider import HMISPHIDataProvider, PHIQueryInspector
from .minimizer import minimize_projection
from .validator import validate_protected_context
from .models import PHIHandlingDecision, ProtectedAIContext
from .exceptions import PHIDataProviderUnavailableError, PHIQueryInspectionError, PHIValidationError
import secrets


class PHIProtectionService:
    LEVEL_ORDER = {level: index for index, level in enumerate(PHILevel)}
    DIRECT_IDENTIFIER_TYPES = frozenset({
        PHIType.PATIENT_NAME, PHIType.PHONE, PHIType.EMAIL, PHIType.ADDRESS,
        PHIType.NATIONAL_ID, PHIType.PASSPORT, PHIType.DATE_OF_BIRTH,
        PHIType.PATIENT_ID, PHIType.MEDICAL_RECORD_NUMBER, PHIType.ENCOUNTER_ID,
    })

    def __init__(self, detector: PHIDetector | None = None, minimizer: PHIMinimizer | None = None, inspector: PHIInspector | None = None, *, provider: HMISPHIDataProvider | None = None, query_inspector: PHIQueryInspector | None = None):
        self.detector = detector or PHIDetector()
        self.minimizer = minimizer or PHIMinimizer()
        self.inspector = inspector or PHIInspector(self.detector)
        self.provider = provider
        self.query_inspector = query_inspector

    async def protect_context(self, *, context: ValidatedRequestContext, capability: str, query: str, purpose: str) -> ProtectedAIContext:
        """Build the only context shape permitted to reach inference."""
        policy = get_projection_policy(capability)
        if not isinstance(context, ValidatedRequestContext):
            raise PHIValidationError("Validated HMIS context is required.")
        if policy.requires_patient_context and (context.patient is None or context.patient_access is None or context.patient_access.status != ContextAccessStatus.ALLOWED):
            raise PHIValidationError("Authorized patient context is required.")
        if policy.requires_encounter_context and (context.encounter is None or context.encounter_access is None or context.encounter_access.status != ContextAccessStatus.ALLOWED):
            raise PHIValidationError("Authorized encounter context is required.")
        if self.query_inspector is None:
            raise PHIQueryInspectionError("A trusted PHI query inspector is required.")
        try:
            protected_query = await self.query_inspector.inspect_query(query=query or "", capability=policy.capability, purpose=purpose)
        except Exception as exc:
            raise PHIQueryInspectionError("The request query could not be inspected safely.") from exc
        if not isinstance(protected_query, str):
            raise PHIQueryInspectionError("The request query inspector returned an invalid result.")
        needs_patient_projection = bool(policy.allowed_patient_fields and context.patient is not None)
        needs_encounter_projection = bool(policy.allowed_encounter_fields and context.encounter is not None)
        if (needs_patient_projection or needs_encounter_projection) and self.provider is None:
            raise PHIDataProviderUnavailableError("An HMIS PHI data provider is required for this capability.")
        patient_data: dict = {}
        encounter_data: dict = {}
        try:
            if needs_patient_projection:
                patient_data = minimize_projection(await self.provider.fetch_patient_projection(context=context, allowed_fields=policy.allowed_patient_fields), policy.allowed_patient_fields, policy.maximum_field_characters)
            if needs_encounter_projection:
                encounter_data = minimize_projection(await self.provider.fetch_encounter_projection(context=context, allowed_fields=policy.allowed_encounter_fields), policy.allowed_encounter_fields, policy.maximum_field_characters)
        except PHIValidationError:
            raise
        except Exception as exc:
            raise PHIDataProviderUnavailableError("The HMIS PHI provider could not be queried safely.") from exc
        result = ProtectedAIContext(
            organization_id=context.organization_id, facility_id=context.facility_id, department_id=context.department_id,
            capability=policy.capability, purpose=purpose.strip(), query=protected_query,
            patient_reference=secrets.token_urlsafe(12) if patient_data else None,
            encounter_reference=secrets.token_urlsafe(12) if encounter_data else None,
            patient_data=patient_data, encounter_data=encounter_data,
            included_patient_fields=tuple(sorted(patient_data)), included_encounter_fields=tuple(sorted(encounter_data)),
            decision=PHIHandlingDecision.ALLOWED, human_review_required=policy.human_review_required,
        )
        validate_protected_context(policy=policy, context=result)
        return result

    async def protect(self, *, principal, request, validated_context):
        return await self.protect_context(context=validated_context, capability=request.capability.value, query=request.query or "", purpose=request.purpose or "")

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
