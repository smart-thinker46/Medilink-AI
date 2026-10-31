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

    def __init__(self, context_provider: HMISContextProvider | None = None, access_authorizer: PatientEncounterAccessAuthorizer | None = None, *, provider: HMISContextProvider | None = None, authorizer: PatientEncounterAccessAuthorizer | None = None):
        self.context_provider = context_provider or provider
        self.access_authorizer = access_authorizer or authorizer
        if self.context_provider is None:
            raise ValueError("An HMIS context provider is required.")
        if self.access_authorizer is None:
            raise ValueError("A patient access authorizer is required.")

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
                patient = await self._provider_call("get_patient", request.patient_id, principal.organization_id)
            except Exception as exc:
                raise ContextProviderUnavailableError() from exc
            if patient is None:
                raise ContextValidationError("The supplied context could not be validated.", "PATIENT_NOT_FOUND")
            GatewayContextValidator.validate_patient_ownership(principal, request, patient)

        if request.encounter_id:
            try:
                encounter = await self._provider_call("get_encounter", request.encounter_id, principal.organization_id)
            except Exception as exc:
                raise ContextProviderUnavailableError() from exc
            if encounter is None:
                raise ContextValidationError("The supplied context could not be validated.", "ENCOUNTER_NOT_FOUND")
            GatewayContextValidator.validate_encounter_ownership(principal, request, encounter, patient)

        GatewayContextValidator.validate_department(principal, request, encounter)
        department = None
        if request.department_id:
            getter = getattr(self.context_provider, "get_department", None)
            if getter is not None:
                try:
                    department = await getter(request.department_id, principal.organization_id, request.facility_id)
                except Exception as exc:
                    raise ContextProviderUnavailableError() from exc
                if department is None:
                    raise ContextValidationError("The supplied context could not be validated.", "DEPARTMENT_NOT_FOUND")
            elif request.department_id not in principal.department_ids:
                raise ContextValidationError("The supplied context could not be validated.", "DEPARTMENT_NOT_AUTHORIZED")
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
            department=department,
            validated_at=datetime.now(timezone.utc),
        )

    async def _provider_call(self, method_name: str, identifier: str, organization_id: str):
        method = getattr(self.context_provider, method_name)
        try:
            return await method(identifier, organization_id)
        except TypeError:
            # Compatibility for existing local adapters while all production
            # providers migrate to organization-scoped method signatures.
            return await method(identifier)

    # Explicit aliases keep call sites readable while preserving one implementation.
    async def validate_context(self, principal: AuthenticatedPrincipal, request: GatewayRequest) -> ValidatedRequestContext:
        return await self.validate(principal, request)

    async def validate_request_context(self, principal: AuthenticatedPrincipal, request: GatewayRequest) -> ValidatedRequestContext:
        return await self.validate(principal, request)

    @staticmethod
    def _require_allowed(decision: ContextAccessDecision, reason: str) -> None:
        if not isinstance(decision, ContextAccessDecision) or decision.status != ContextAccessStatus.ALLOWED:
            raise ContextValidationError("The supplied context could not be validated.", reason)


ContextIntegrationService = ContextValidationService
