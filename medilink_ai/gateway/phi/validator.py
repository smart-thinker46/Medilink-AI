from __future__ import annotations

from .exceptions import PHIValidationError
from .models import PHIHandlingDecision, PHIProtectionPolicy, ProtectedAIContext


def validate_protected_context(*, policy: PHIProtectionPolicy, context: ProtectedAIContext) -> None:
    if context.capability != policy.capability:
        raise PHIValidationError("Protected context capability does not match its policy.")
    if not context.organization_id or not context.facility_id:
        raise PHIValidationError("Protected context is missing its organization or facility.")
    if not context.purpose.strip() or not isinstance(context.query, str):
        raise PHIValidationError("Protected context has no declared purpose or query.")
    if context.decision != PHIHandlingDecision.ALLOWED:
        raise PHIValidationError("Protected context has not been approved for inference.")
    returned_patient = tuple(sorted(context.patient_data))
    returned_encounter = tuple(sorted(context.encounter_data))
    if context.included_patient_fields != returned_patient or context.included_encounter_fields != returned_encounter:
        raise PHIValidationError("Protected field manifest does not match the protected data.")
    if not set(returned_patient).issubset(policy.allowed_patient_fields) or not set(returned_encounter).issubset(policy.allowed_encounter_fields):
        raise PHIValidationError("Protected context contains fields outside its policy.")
    if policy.requires_patient_context and not context.patient_reference:
        raise PHIValidationError("Protected context is missing its patient reference.")
    if policy.requires_encounter_context and not context.encounter_reference:
        raise PHIValidationError("Protected context is missing its encounter reference.")
    if not policy.allowed_patient_fields and returned_patient:
        raise PHIValidationError("This capability does not permit patient fields.")
    if not policy.allowed_encounter_fields and returned_encounter:
        raise PHIValidationError("This capability does not permit encounter fields.")
