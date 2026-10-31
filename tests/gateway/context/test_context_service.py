import asyncio
import pytest

from medilink_ai.gateway import AuthenticatedPrincipal, GatewayRequest
from medilink_ai.gateway.context import (
    ContextAccessDecision,
    ContextAccessStatus,
    ContextAuthorizationUnavailableError,
    ContextValidationService,
    EncounterContextRecord,
    PatientContextRecord,
)
from medilink_ai.gateway.context.exceptions import ContextProviderUnavailableError, ContextValidationError


class FakeProvider:
    def __init__(self, *, unavailable=False):
        self.unavailable = unavailable

    async def get_patient(self, patient_id):
        if self.unavailable:
            raise RuntimeError("HMIS unavailable")
        return PatientContextRecord(patient_id, "org-001", "facility-001")

    async def get_encounter(self, encounter_id):
        return EncounterContextRecord(encounter_id, "patient-001", "org-001", "facility-001")


class FakeAuthorizer:
    def __init__(self, status=ContextAccessStatus.ALLOWED, *, unavailable=False):
        self.status, self.unavailable = status, unavailable

    async def authorize_patient(self, principal, patient, purpose):
        if self.unavailable:
            raise RuntimeError("authorization unavailable")
        return ContextAccessDecision(self.status)

    async def authorize_encounter(self, principal, encounter, purpose):
        return ContextAccessDecision(self.status)


def principal():
    return AuthenticatedPrincipal("doctor-001", "org-001", frozenset({"facility-001"}), frozenset({"clinical"}))


def request(**changes):
    values = {"capability": "patient.summary", "module": "clinical", "facility_id": "facility-001", "department_id": "clinical", "patient_id": "patient-001", "encounter_id": "encounter-001", "purpose": "care delivery"}
    values.update(changes)
    return GatewayRequest(**values)


def test_service_returns_only_validated_context():
    result = asyncio.run(ContextValidationService(FakeProvider(), FakeAuthorizer()).validate(principal(), request()))
    assert result.organization_id == "org-001"
    assert result.patient_id == "patient-001"
    assert result.encounter_id == "encounter-001"
    assert result.validated_at is not None


def test_missing_purpose_is_rejected():
    with pytest.raises(ContextValidationError) as error:
        asyncio.run(ContextValidationService(FakeProvider(), FakeAuthorizer()).validate(principal(), request(purpose="")))
    assert error.value.reason_code == "PURPOSE_REQUIRED"


def test_provider_failure_fails_closed():
    with pytest.raises(ContextProviderUnavailableError):
        asyncio.run(ContextValidationService(FakeProvider(unavailable=True), FakeAuthorizer()).validate(principal(), request()))


def test_access_denial_fails_closed():
    with pytest.raises(ContextValidationError) as error:
        asyncio.run(ContextValidationService(FakeProvider(), FakeAuthorizer(ContextAccessStatus.DENIED)).validate(principal(), request()))
    assert error.value.reason_code == "PATIENT_ACCESS_DENIED"


def test_authorizer_failure_fails_closed():
    with pytest.raises(ContextAuthorizationUnavailableError):
        asyncio.run(ContextValidationService(FakeProvider(), FakeAuthorizer(unavailable=True)).validate(principal(), request()))
