from __future__ import annotations

from datetime import datetime, timezone

from ..models import AuthenticatedPrincipal
from ..capability_registry import get_capability_policy
from ..schemas import GatewayRequest
from .exceptions import (
    ContextAuthorizationUnavailableError,
    ContextProviderUnavailableError,
    ContextValidationError,
)
from .models import ContextAccessDecision, ContextAccessStatus, ValidatedRequestContext
from .provider import HMISContextProvider, PatientEncounterAccessAuthorizer
from .validator import GatewayContextValidator


class ContextValidationService:
    """Retrieves authoritative context, validates ownership, then access."""

    def __init__(self, context_provider: HMISContextProvider, access_authorizer: PatientEncounterAccessAuthorizer):
        self.context_provider = context_provider
        self.access_authorizer = access_authorizer

    async def validate(self, principal: AuthenticatedPrincipal, request: GatewayRequest) -> ValidatedRequestContext:
        GatewayContextValidator.validate_principal_facility(principal, request.facility_id)
        policy = get_capability_policy(request.capability)
        if request.module.lower() not in policy.allowed_modules:
            raise ContextValidationError("The supplied context could not be validated.", "MODULE_ACCESS_DENIED")
        if not request.purpose or not request.purpose.strip():
            raise ContextValidationError("The supplied context could not be validated.", "PURPOSE_REQUIRED")

        patient = None
        encounter = None
        if request.patient_id:
            try:
                patient = await self.context_provider.get_patient(request.patient_id)
            except Exception as exc:
                raise ContextProviderUnavailableError() from exc
            if patient is None:
                raise ContextValidationError("The supplied context could not be validated.", "PATIENT_NOT_FOUND")
            GatewayContextValidator.validate_patient_ownership(principal, request, patient)

        if request.encounter_id:
            try:
                encounter = await self.context_provider.get_encounter(request.encounter_id)
            except Exception as exc:
                raise ContextProviderUnavailableError() from exc
            if encounter is None:
                raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_NOT_FOUND")
            GatewayContextValidator.validate_encounter_ownership(principal, request, encounter, patient)

        GatewayContextValidator.validate_department(principal, request, encounter)
        patient_access = None
        encounter_access = None
        try:
            if patient is not None:
                patient_access = await self.access_authorizer.authorize_patient(principal, patient, request.purpose.strip())
                self._require_allowed(patient_access, "PATIENT_ACCESS_DENIED")
            if encounter is not None:
                encounter_access = await self.access_authorizer.authorize_encounter(principal, encounter, request.purpose.strip())
                self._require_allowed(encounter_access, "ENCOUNTER_ACCESS_DENIED")
        except ContextValidationError:
            raise
        except Exception as exc:
            raise ContextAuthorizationUnavailableError() from exc

        return ValidatedRequestContext(
            organization_id=principal.organization_id,
            facility_id=request.facility_id,
            department_id=request.department_id,
            patient=patient,
            encounter=encounter,
            purpose=request.purpose.strip(),
            patient_access=patient_access,
            encounter_access=encounter_access,
            validated_at=datetime.now(timezone.utc),
        )

    # Explicit aliases keep call sites readable while preserving one implementation.
    async def validate_context(self, principal: AuthenticatedPrincipal, request: GatewayRequest) -> ValidatedRequestContext:
        return await self.validate(principal, request)

    async def validate_request_context(self, principal: AuthenticatedPrincipal, request: GatewayRequest) -> ValidatedRequestContext:
        return await self.validate(principal, request)

    @staticmethod
    def _require_allowed(decision: ContextAccessDecision, reason: str) -> None:
        if not isinstance(decision, ContextAccessDecision) or decision.status != ContextAccessStatus.ALLOWED:
            raise ContextValidationError("The supplied context could not be validated.", reason)
