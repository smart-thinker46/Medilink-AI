from __future__ import annotations

from ..models import AuthenticatedPrincipal
from ..schemas import GatewayRequest
from .exceptions import ContextValidationError
from .models import EncounterContextRecord, PatientContextRecord


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
