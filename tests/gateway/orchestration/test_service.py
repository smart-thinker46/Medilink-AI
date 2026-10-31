from dataclasses import dataclass

import asyncio

from medilink_ai.gateway import AICapability, AuthenticatedPrincipal, GatewayAuthorizationService, GatewayRequest
from medilink_ai.gateway.orchestration import GatewayExecutionStatus, GatewayOrchestrator, GatewayStage
from medilink_ai.gateway.safety import AISafetyService
from medilink_ai.gateway.audit import AuditService, InMemoryAuditSink
from medilink_ai.gateway.context import (ContextAccessDecision, ContextAccessStatus, EncounterContextRecord, PatientContextRecord, ValidatedRequestContext)
from medilink_ai.gateway.phi import PHIHandlingDecision, ProtectedAIContext


def principal(*permissions):
    return AuthenticatedPrincipal(
        "doctor-001", "org-001", frozenset({"facility-001"}), frozenset({"clinical"}),
        frozenset({"DOCTOR"}), frozenset({"ai:use", *permissions}),
    )


@dataclass
class FakeContext:
    fail: bool = False

    async def validate(self, *, principal, request):
        if self.fail:
            raise RuntimeError("context unavailable")
        patient = PatientContextRecord(request.patient_id, principal.organization_id, request.facility_id) if request.patient_id else None
        encounter = EncounterContextRecord(request.encounter_id, request.patient_id, principal.organization_id, request.facility_id, request.department_id) if request.encounter_id else None
        allowed = ContextAccessDecision(ContextAccessStatus.ALLOWED)
        return ValidatedRequestContext(
            principal.organization_id, request.facility_id, request.department_id,
            patient, encounter, request.purpose or "test purpose",
            allowed if patient else None, allowed if encounter else None,
        )


@dataclass
class FakePHI:
    fail: bool = False

    async def protect(self, *, principal, request, validated_context):
        if self.fail:
            raise RuntimeError("phi unavailable")
        return ProtectedAIContext(
            organization_id=validated_context.organization_id,
            facility_id=validated_context.facility_id,
            department_id=validated_context.department_id,
            capability=request.capability.value,
            purpose=(request.purpose or "").strip(),
            query=request.query or "",
            patient_reference="patient-ref" if validated_context.patient else None,
            encounter_reference="encounter-ref" if validated_context.encounter else None,
            decision=PHIHandlingDecision.ALLOWED,
            human_review_required=request.capability == AICapability.DOCUMENTATION_DRAFT,
        )


class FakeExecutor:
    def __init__(self):
        self.calls = 0

    async def execute(self, **kwargs):
        self.calls += 1
        return {"draft": True}


def request(capability=AICapability.KNOWLEDGE_ASK, query="Explain the pharmacy procedure", **kwargs):
    kwargs.setdefault("purpose", "Test an approved AI workflow")
    return GatewayRequest(capability=capability, module="clinical", facility_id="facility-001", query=query, **kwargs)


def run(request_value, *, user=None, context=None, phi=None, executor=None):
    executor = executor or FakeExecutor()
    result = asyncio.run(GatewayOrchestrator(
        GatewayAuthorizationService(), context or FakeContext(), phi or FakePHI(), AISafetyService(), executor,
    ).execute(principal=user or principal("ai:capability:knowledge.ask", "ai:knowledge:ask", "ai:patient_summary"), request=request_value))
    return result, executor


def test_pipeline_runs_stages_in_order_for_allowed_request():
    result, executor = run(request())
    assert result.status == GatewayExecutionStatus.COMPLETED
    assert [stage.stage for stage in result.stages] == [
        GatewayStage.AUTHENTICATION, GatewayStage.AUTHORIZATION, GatewayStage.CONTEXT_VALIDATION,
        GatewayStage.PHI_PROTECTION, GatewayStage.SAFETY_CLASSIFICATION, GatewayStage.EXECUTION,
    ]
    assert executor.calls == 1


def test_critical_action_is_blocked_before_execution():
    result, executor = run(request(query="Approve this patient's discharge"))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert executor.calls == 0
    assert result.stages[-1].stage == GatewayStage.SAFETY_CLASSIFICATION


def test_context_failure_is_fail_closed():
    result, executor = run(request(), context=FakeContext(fail=True))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert result.reason_codes == ("CONTEXT_VALIDATION_FAILED",)
    assert executor.calls == 0


def test_phi_failure_is_fail_closed():
    result, executor = run(request(), phi=FakePHI(fail=True))
    assert result.status == GatewayExecutionStatus.BLOCKED
    assert result.reason_codes == ("PHI_PROTECTION_FAILED",)
    assert executor.calls == 0


def test_review_request_reaches_executor_with_review_flag():
    result, executor = run(request(AICapability.DOCUMENTATION_DRAFT, "Draft a clinical note", patient_id="patient-001", encounter_id="encounter-001"), user=principal("ai:capability:documentation.draft", "ai:documentation:draft"))
    assert result.status == GatewayExecutionStatus.REVIEW_REQUIRED
    assert result.human_review_required is True
    assert executor.calls == 1


def test_configured_audit_sink_receives_request_and_completion():
    sink = InMemoryAuditSink()
    executor = FakeExecutor()
    orchestrator = GatewayOrchestrator(
        GatewayAuthorizationService(), FakeContext(), FakePHI(), AISafetyService(), executor,
        audit_service=AuditService(sink),
    )
    result = asyncio.run(orchestrator.execute(principal=principal("ai:knowledge:ask"), request=request()))
    assert result.status == GatewayExecutionStatus.COMPLETED
    assert [event.event_type.value for event in sink.events][:2] == ["REQUEST_RECEIVED", "AUTHENTICATION"]
    assert sink.events[-1].event_type.value == "REQUEST_COMPLETED"
