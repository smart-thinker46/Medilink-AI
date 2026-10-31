import asyncio

from medilink_ai.gateway.orchestration import GatewayExecutionStatus

from .conftest import make_orchestrator
from .fakes import FakeExecutor, FakePHIService
from medilink_ai.gateway.phi import PHIHandlingDecision, ProtectedAIContext
from medilink_ai.gateway.routing import ProtectedModelInput


def test_phi_failure_fails_closed(authorized_principal, patient_summary_request):
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(phi=FakePHIService(error=RuntimeError("PHI unavailable")), executor=executor).execute(principal=authorized_principal, request=patient_summary_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert result.reason_codes == ("PHI_PROTECTION_FAILED",)
    assert executor.calls == []


def test_minimum_necessary_context_is_forwarded(authorized_principal, patient_summary_request):
    protected = ProtectedAIContext(
        organization_id="org-001",
        facility_id="facility-001",
        department_id="clinical",
        capability="patient.summary",
        purpose="Prepare a clinical handover summary",
        query="Summarize the recent encounter.",
        patient_reference="patient-ref",
        encounter_reference="encounter-ref",
        patient_data={"age_band": "40-49"},
        encounter_data={"diagnoses": ["hypertension"], "active_medications": ["amlodipine"]},
        included_patient_fields=("age_band",),
        included_encounter_fields=("active_medications", "diagnoses"),
        decision=PHIHandlingDecision.ALLOWED,
        human_review_required=True,
    )
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(phi=FakePHIService(result=protected), executor=executor).execute(principal=authorized_principal, request=patient_summary_request))
    assert result.status == GatewayExecutionStatus.REVIEW_REQUIRED
    model_input = executor.calls[0]["protected"]
    assert isinstance(model_input, ProtectedModelInput)
    assert model_input.query == protected.query
    assert model_input.patient_data == protected.patient_data
    assert model_input.encounter_data == protected.encounter_data
    assert not hasattr(model_input, "organization_id")
    assert not hasattr(model_input, "patient_id")
    assert "national_id" not in model_input.patient_data
    assert "phone" not in model_input.patient_data



def test_missing_protected_query_blocks_instead_of_using_original_request(authorized_principal, knowledge_request):
    from medilink_ai.gateway.phi import ProtectedAIContext, PHIHandlingDecision

    malformed = ProtectedAIContext(
        organization_id="org-001",
        facility_id="facility-001",
        department_id="clinical",
        capability="knowledge.ask",
        purpose=knowledge_request.purpose,
        query="",
        decision=PHIHandlingDecision.ALLOWED,
    )
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(phi=FakePHIService(result=malformed), executor=executor).execute(principal=authorized_principal, request=knowledge_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert executor.calls == []


def test_protected_context_cannot_change_tenant_or_facility(authorized_principal, patient_summary_request):
    from medilink_ai.gateway.phi import PHIHandlingDecision, ProtectedAIContext

    protected = ProtectedAIContext(
        organization_id="org-OTHER",
        facility_id="facility-001",
        department_id="clinical",
        capability="patient.summary",
        purpose=patient_summary_request.purpose,
        query="Summarize the encounter.",
        patient_reference="patient-ref",
        encounter_reference="encounter-ref",
        patient_data={"age_band": "40-49"},
        encounter_data={"diagnoses": ["synthetic"]},
        included_patient_fields=("age_band",),
        included_encounter_fields=("diagnoses",),
        decision=PHIHandlingDecision.ALLOWED,
        human_review_required=True,
    )
    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(phi=FakePHIService(result=protected), executor=executor).execute(principal=authorized_principal, request=patient_summary_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert result.reason_codes == ("PHI_VALIDATION_FAILED",)
    assert executor.calls == []


def test_legacy_text_only_phi_service_is_rejected(authorized_principal, knowledge_request):
    class TextOnlyPHI:
        def protect_text(self, *, capability, text):
            return text

    executor = FakeExecutor()
    result = asyncio.run(make_orchestrator(phi=TextOnlyPHI(), executor=executor).execute(principal=authorized_principal, request=knowledge_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert executor.calls == []



def test_noncanonical_context_mapping_is_not_treated_as_patient_authorization(authorized_principal, patient_summary_request):
    from .fakes import FakeContextService

    executor = FakeExecutor()
    legacy_context = {"organization_id": "org-001", "facility_id": "facility-001"}
    result = asyncio.run(make_orchestrator(
        context=FakeContextService(result=legacy_context),
        executor=executor,
    ).execute(principal=authorized_principal, request=patient_summary_request))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert result.reason_codes == ("CANONICAL_CONTEXT_REQUIRED",)
    assert executor.calls == []

