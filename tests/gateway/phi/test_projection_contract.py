import asyncio
import pytest

from medilink_ai.gateway.context import ContextAccessDecision, ContextAccessStatus, EncounterContextRecord, PatientContextRecord, ValidatedRequestContext
from medilink_ai.gateway.phi import PHIProtectionService
from medilink_ai.gateway.phi.exceptions import PHIQueryInspectionError, PHIValidationError


class Provider:
    async def fetch_patient_projection(self, *, context, allowed_fields):
        return {"age_band": "40-49", "national_id": "must-not-return"}

    async def fetch_encounter_projection(self, *, context, allowed_fields):
        return {"diagnoses": ["example"]}


class Inspector:
    async def inspect_query(self, *, query, capability, purpose):
        return query.replace("John Doe", "[PATIENT]")


def context():
    patient = PatientContextRecord("p-1", "org-1", "facility-1")
    encounter = EncounterContextRecord("e-1", "p-1", "org-1", "facility-1", "clinical")
    allowed = ContextAccessDecision(ContextAccessStatus.ALLOWED)
    return ValidatedRequestContext("org-1", "facility-1", "clinical", patient, encounter, "handover", allowed, allowed)


def test_projection_requires_query_inspection():
    with pytest.raises(PHIQueryInspectionError):
        asyncio.run(PHIProtectionService(provider=Provider()).protect_context(context=context(), capability="patient.summary", query="summary", purpose="handover"))


def test_unapproved_provider_field_is_rejected():
    with pytest.raises(PHIValidationError):
        asyncio.run(PHIProtectionService(provider=Provider(), query_inspector=Inspector()).protect_context(context=context(), capability="patient.summary", query="Summarize John Doe", purpose="handover"))



def test_knowledge_capability_does_not_require_patient_data_provider():
    from medilink_ai.gateway.context import ValidatedRequestContext
    from medilink_ai.gateway.phi import PHIHandlingDecision

    clean_context = ValidatedRequestContext(
        organization_id="org-1",
        facility_id="facility-1",
        department_id="clinical",
        patient=None,
        encounter=None,
        purpose="Understand a pharmacy SOP",
    )
    result = asyncio.run(PHIProtectionService(query_inspector=Inspector()).protect_context(
        context=clean_context,
        capability="knowledge.ask",
        query="Explain the pharmacy POS procedure.",
        purpose="Understand a pharmacy SOP",
    ))
    assert result.decision == PHIHandlingDecision.ALLOWED
    assert result.patient_data == {}
    assert result.encounter_data == {}


def test_required_patient_reference_cannot_be_omitted():
    from medilink_ai.gateway.phi import PHIHandlingDecision, ProtectedAIContext
    from medilink_ai.gateway.phi.policies import get_phi_policy
    from medilink_ai.gateway.phi.validator import validate_protected_context

    invalid = ProtectedAIContext(
        organization_id="org-1",
        facility_id="facility-1",
        department_id="clinical",
        capability="patient.summary",
        purpose="handover",
        query="Summarize the encounter.",
        encounter_reference="encounter-ref",
        patient_data={"age_band": "40-49"},
        encounter_data={"diagnoses": ["synthetic"]},
        included_patient_fields=("age_band",),
        included_encounter_fields=("diagnoses",),
        decision=PHIHandlingDecision.ALLOWED,
    )
    with pytest.raises(PHIValidationError):
        validate_protected_context(policy=get_phi_policy("patient.summary"), context=invalid)

