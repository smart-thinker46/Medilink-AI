from __future__ import annotations

from ..models import AuthenticatedPrincipal
from ..schemas import GatewayRequest
from .exceptions import ContextValidationError
from .models import DepartmentContextRecord, EncounterContextRecord, PatientContextRecord, ValidatedRequestContext


class GatewayContextValidator:
    """Pure relationship validation for canonical records and a request."""

    @staticmethod
    def validate_principal_facility(principal: AuthenticatedPrincipal, requested_facility_id: str) -> None:
        if not principal.subject_id:
            raise ContextValidationError("The supplied context could not be validated.", "INVALID_PRINCIPAL")
        if not principal.organization_id:
            raise ContextValidationError("The supplied context could not be validated.", "INVALID_ORGANIZATION")
        if requested_facility_id not in principal.facility_ids:
            raise ContextValidationError("The supplied context could not be validated.", "FACILITY_NOT_AUTHORIZED")

    @staticmethod
    def validate_department(principal: AuthenticatedPrincipal, request: GatewayRequest, encounter: EncounterContextRecord | None = None) -> None:
        if request.department_id and request.department_id not in principal.department_ids:
            raise ContextValidationError("The supplied context could not be validated.", "DEPARTMENT_NOT_AUTHORIZED")
        if encounter and encounter.department_id and request.department_id and encounter.department_id != request.department_id:
            raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_DEPARTMENT_MISMATCH")

    @staticmethod
    def validate_patient_ownership(principal: AuthenticatedPrincipal, request: GatewayRequest, patient: PatientContextRecord) -> None:
        if not request.patient_id or patient.patient_id != request.patient_id:
            raise ContextValidationError("The supplied context could not be validated.", "PATIENT_NOT_FOUND")
        if patient.organization_id != principal.organization_id:
            raise ContextValidationError("The supplied context could not be validated.", "PATIENT_ORGANIZATION_MISMATCH")
        if patient.facility_id != request.facility_id:
            raise ContextValidationError("The supplied context could not be validated.", "PATIENT_FACILITY_MISMATCH")

    @staticmethod
    def validate_encounter_ownership(
        principal: AuthenticatedPrincipal,
        request: GatewayRequest,
        encounter: EncounterContextRecord,
        patient: PatientContextRecord | None,
    ) -> None:
        if not request.encounter_id or encounter.encounter_id != request.encounter_id:
            raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_NOT_FOUND")
        if patient is None or encounter.patient_id != patient.patient_id:
            raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_PATIENT_MISMATCH")
        if encounter.organization_id != principal.organization_id:
            raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_ORGANIZATION_MISMATCH")
        if encounter.facility_id != request.facility_id:
            raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_FACILITY_MISMATCH")

    @staticmethod
    def validate_department_record(principal: AuthenticatedPrincipal, request: GatewayRequest, department: DepartmentContextRecord | None) -> None:
        if not request.department_id:
            return
        if department is None:
            raise ContextValidationError("The supplied context could not be validated.", "DEPARTMENT_NOT_FOUND")
        if department.department_id != request.department_id:
            raise ContextValidationError("The supplied context could not be validated.", "DEPARTMENT_NOT_FOUND")
        if department.organization_id != principal.organization_id:
            raise ContextValidationError("The supplied context could not be validated.", "DEPARTMENT_ORGANIZATION_MISMATCH")
        if department.facility_id != request.facility_id:
            raise ContextValidationError("The supplied context could not be validated.", "DEPARTMENT_FACILITY_MISMATCH")


def validate_context_records(*, principal: AuthenticatedPrincipal, request: GatewayRequest,
                             patient: PatientContextRecord | None,
                             encounter: EncounterContextRecord | None,
                             department: DepartmentContextRecord | None = None,
                             patient_access_verified: bool = False,
                             encounter_access_verified: bool = False) -> ValidatedRequestContext:
    """Validate resolved records and return a canonical, trusted context."""
    GatewayContextValidator.validate_principal_facility(principal, request.facility_id)
    if request.patient_id:
        if patient is None:
            raise ContextValidationError("The supplied context could not be validated.", "PATIENT_NOT_FOUND")
        GatewayContextValidator.validate_patient_ownership(principal, request, patient)
        if not patient_access_verified:
            raise ContextValidationError("The supplied context could not be validated.", "PATIENT_ACCESS_DENIED")
    if request.encounter_id:
        if encounter is None:
            raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_NOT_FOUND")
        GatewayContextValidator.validate_encounter_ownership(principal, request, encounter, patient)
        if not encounter_access_verified:
            raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_ACCESS_DENIED")
    GatewayContextValidator.validate_department(principal, request, encounter)
    GatewayContextValidator.validate_department_record(principal, request, department)
    if not request.purpose or not request.purpose.strip():
        raise ContextValidationError("The supplied context could not be validated.", "PURPOSE_REQUIRED")
    return ValidatedRequestContext(
        organization_id=principal.organization_id,
        facility_id=request.facility_id,
        department_id=request.department_id,
        patient=patient,
        encounter=encounter,
        purpose=request.purpose.strip(),
        department=department,
    )
