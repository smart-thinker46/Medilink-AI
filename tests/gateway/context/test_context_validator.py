import pytest

from medilink_ai.gateway import AuthenticatedPrincipal, GatewayRequest
from medilink_ai.gateway.context import (
    DepartmentContextRecord,
    EncounterContextRecord,
    GatewayContextValidator,
    PatientContextRecord,
)
from medilink_ai.gateway.context.exceptions import ContextValidationError


@pytest.fixture
def principal():
    return AuthenticatedPrincipal(
        "doctor-001", "org-001", frozenset({"facility-001"}), frozenset({"clinical"})
    )


def request(**changes):
    values = {
        "capability": "patient.summary", "module": "clinical",
        "facility_id": "facility-001", "department_id": "clinical",
        "patient_id": "patient-001", "encounter_id": "encounter-001",
        "purpose": "care delivery",
    }
    values.update(changes)
    return GatewayRequest(**values)


def patient(**changes):
    values = {"patient_id": "patient-001", "organization_id": "org-001", "facility_id": "facility-001"}
    values.update(changes)
    return PatientContextRecord(**values)


def encounter(**changes):
    values = {"encounter_id": "encounter-001", "patient_id": "patient-001", "organization_id": "org-001", "facility_id": "facility-001"}
    values.update(changes)
    return EncounterContextRecord(**values)


def test_valid_relationships_are_accepted(principal):
    GatewayContextValidator.validate_principal_facility(principal, "facility-001")
    GatewayContextValidator.validate_patient_ownership(principal, request(), patient())
    GatewayContextValidator.validate_encounter_ownership(principal, request(), encounter(), patient())


def test_department_must_belong_to_requested_facility(principal):
    with pytest.raises(ContextValidationError) as error:
        GatewayContextValidator.validate_department_record(
            principal, request(), DepartmentContextRecord("clinical", "org-001", "facility-999")
        )
    assert error.value.reason_code == "DEPARTMENT_FACILITY_MISMATCH"


@pytest.mark.parametrize("record_changes,code", [
    ({"organization_id": "org-999"}, "PATIENT_ORGANIZATION_MISMATCH"),
    ({"facility_id": "facility-999"}, "PATIENT_FACILITY_MISMATCH"),
])
def test_patient_ownership_isolation(principal, record_changes, code):
    with pytest.raises(ContextValidationError, match="could not be validated") as error:
        GatewayContextValidator.validate_patient_ownership(principal, request(), patient(**record_changes))
    assert error.value.reason_code == code


def test_encounter_cannot_belong_to_another_patient(principal):
    with pytest.raises(ContextValidationError) as error:
        GatewayContextValidator.validate_encounter_ownership(principal, request(), encounter(patient_id="patient-999"), patient())
    assert error.value.reason_code == "ENCOUNTER_PATIENT_MISMATCH"
