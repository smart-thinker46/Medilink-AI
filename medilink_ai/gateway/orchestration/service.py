from __future__ import annotations

import inspect
from typing import Any, Protocol

from ..authorization_service import GatewayAuthorizationService
from ..models import AuthenticatedPrincipal, GatewayDecisionStatus
from ..schemas import GatewayRequest
from ..safety.models import AISafetyDecision
from ..safety.service import AISafetyService
from ..output.service import AIOutputValidationService
from ..audit.builder import build_gateway_audit_event
from ..audit.models import AuditEventType, AuditOutcome, AuditSeverity
from ..audit.service import AuditService
from ..context.models import ContextAccessStatus, ValidatedRequestContext
from ..phi.exceptions import PHIDataProviderUnavailableError, PHIQueryInspectionError, PHIPolicyError, PHIValidationError
from ..phi.models import PHIHandlingDecision, ProtectedAIContext
from ..phi.policies import get_phi_policy as get_projection_policy
from ..phi.validator import validate_protected_context
from ..routing.models import ProtectedModelInput
from .models import GatewayExecutionStatus, GatewayStage, OrchestrationResult, StageResult
from .stages import StageTimer


class AIRequestExecutor(Protocol):
    async def execute(self, *, request: GatewayRequest, principal: AuthenticatedPrincipal, validated_context: Any, protected_request: Any) -> Any:
        ...


class ContextValidationDependency(Protocol):
    async def validate(self, *, principal: AuthenticatedPrincipal, request: GatewayRequest) -> Any:
        ...


class PHIProtectionDependency(Protocol):
    async def protect(self, *, principal: AuthenticatedPrincipal, request: GatewayRequest, validated_context: Any) -> Any:
        ...


class GatewayOrchestrator:
    """Runs every mandatory Gateway control in a fixed, fail-closed order."""

    def __init__(self, authorization_service: GatewayAuthorizationService, context_service: ContextValidationDependency, phi_service: Any, safety_service: AISafetyService, executor: AIRequestExecutor, output_validator: AIOutputValidationService | None = None, audit_service: AuditService | None = None, metrics: Any | None = None):
        self.authorization_service = authorization_service
        self.context_service = context_service
        self.phi_service = phi_service
        self.safety_service = safety_service
        self.executor = executor
        self.output_validator = output_validator
        self.audit_service = audit_service
        self.metrics = metrics

    def _record_event(self, *, event_type: AuditEventType, request: GatewayRequest, principal: AuthenticatedPrincipal | None, outcome: AuditOutcome, stage: str | None = None, reasons: tuple[str, ...] = (), severity: AuditSeverity = AuditSeverity.INFO, metadata: dict | None = None) -> None:
        if self.audit_service is None:
            return
        event = build_gateway_audit_event(
            event_type=event_type, request_id=str(request.request_id), outcome=outcome,
            actor_id=principal.subject_id if principal else None,
            organization_id=principal.organization_id if principal else None,
            facility_id=request.facility_id, department_id=request.department_id,
            module=request.module, capability=request.capability.value,
            purpose_category="provided" if request.purpose else None,
            patient_id=request.patient_id, encounter_id=request.encounter_id,
            stage=stage, reason_codes=reasons, severity=severity, metadata=metadata,
        )
        # Audit failures intentionally propagate: security decisions must not be unrecorded.
        self.audit_service.record(event)

    def _result(self, request: GatewayRequest, status: GatewayExecutionStatus, stages: list[StageResult], reasons: tuple[str, ...] = (), review: bool = False, output: Any = None, principal: AuthenticatedPrincipal | None = None) -> OrchestrationResult:
        if self.audit_service is not None:
            for stage_result in stages:
                event_type = {
                    GatewayStage.AUTHENTICATION: AuditEventType.AUTHENTICATION,
                    GatewayStage.AUTHORIZATION: AuditEventType.AUTHORIZATION,
                    GatewayStage.CONTEXT_VALIDATION: AuditEventType.CONTEXT_VALIDATED,
                    GatewayStage.PHI_PROTECTION: AuditEventType.PHI_PROTECTED,
                    GatewayStage.SAFETY_CLASSIFICATION: AuditEventType.SAFETY_CLASSIFIED,
                    GatewayStage.EXECUTION: AuditEventType.INFERENCE_COMPLETED,
                    GatewayStage.OUTPUT_VALIDATION: AuditEventType.OUTPUT_VALIDATED,
                }[stage_result.stage]
                outcome = AuditOutcome.REVIEW_REQUIRED if stage_result.status == GatewayExecutionStatus.REVIEW_REQUIRED else AuditOutcome.SUCCESS
                if stage_result.status == GatewayExecutionStatus.BLOCKED:
                    outcome = AuditOutcome.BLOCKED
                elif stage_result.status == GatewayExecutionStatus.FAILED:
                    outcome = AuditOutcome.FAILED
                self._record_event(event_type=event_type, request=request, principal=principal, outcome=outcome, stage=stage_result.stage.value, reasons=stage_result.reason_codes, severity=AuditSeverity.SECURITY if outcome in {AuditOutcome.BLOCKED, AuditOutcome.DENIED} else AuditSeverity.INFO, metadata={"stage_status": stage_result.status.value} if stage_result.status else None)
            final_event = AuditEventType.REQUEST_COMPLETED if status in {GatewayExecutionStatus.COMPLETED, GatewayExecutionStatus.REVIEW_REQUIRED} else AuditEventType.REQUEST_BLOCKED if status == GatewayExecutionStatus.BLOCKED else AuditEventType.REQUEST_FAILED
            final_outcome = AuditOutcome.REVIEW_REQUIRED if status == GatewayExecutionStatus.REVIEW_REQUIRED else AuditOutcome.SUCCESS if status == GatewayExecutionStatus.COMPLETED else AuditOutcome.BLOCKED if status == GatewayExecutionStatus.BLOCKED else AuditOutcome.FAILED
            self._record_event(event_type=final_event, request=request, principal=principal, outcome=final_outcome, stage="ORCHESTRATION", reasons=reasons, severity=AuditSeverity.SECURITY if status == GatewayExecutionStatus.BLOCKED else AuditSeverity.INFO, metadata={"review_required": review})
        return OrchestrationResult(str(request.request_id), status, tuple(stages), reasons, review, output)

    async def execute(self, *, principal: AuthenticatedPrincipal, request: GatewayRequest) -> OrchestrationResult:
        stages: list[StageResult] = []
        self._record_event(event_type=AuditEventType.REQUEST_RECEIVED, request=request, principal=principal, outcome=AuditOutcome.SUCCESS, stage="ORCHESTRATION")

        timer = StageTimer(GatewayStage.AUTHENTICATION); timer.start()
        if not principal or not principal.subject_id or not principal.organization_id:
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, ("AUTHENTICATION_FAILED",)))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, ("AUTHENTICATION_FAILED",), principal=principal)
        stages.append(timer.finish(GatewayExecutionStatus.COMPLETED))

        # The initial authorization pass must not trust request-body verification flags.
        auth_timer = StageTimer(GatewayStage.AUTHORIZATION); auth_timer.start()
        preliminary = self.authorization_service.authorize(principal, request)
        verification_only = {"PATIENT_ACCESS_NOT_VERIFIED", "ENCOUNTER_ACCESS_NOT_VERIFIED"}
        non_context_denials = tuple(code for code in preliminary.reason_codes if code not in verification_only)
        if preliminary.status != GatewayDecisionStatus.ALLOWED and non_context_denials:
            stages.append(auth_timer.finish(GatewayExecutionStatus.BLOCKED, non_context_denials))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, non_context_denials, principal=principal)
        auth_stage_index = len(stages)
        stages.append(auth_timer.finish(
            GatewayExecutionStatus.REVIEW_REQUIRED if preliminary.status != GatewayDecisionStatus.ALLOWED else GatewayExecutionStatus.COMPLETED,
            ("TRUSTED_CONTEXT_VERIFICATION_DEFERRED",) if preliminary.status != GatewayDecisionStatus.ALLOWED else (),
        ))

        context_timer = StageTimer(GatewayStage.CONTEXT_VALIDATION); context_timer.start()
        try:
            context = await self.context_service.validate(principal=principal, request=request)
        except Exception:
            reasons = ("CONTEXT_VALIDATION_FAILED",)
            stages.append(context_timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        stages.append(context_timer.finish(GatewayExecutionStatus.COMPLETED))

        if not isinstance(context, ValidatedRequestContext):
            reasons = ("CANONICAL_CONTEXT_REQUIRED",)
            stages[-1] = StageResult(GatewayStage.CONTEXT_VALIDATION, GatewayExecutionStatus.BLOCKED, reasons, stages[-1].duration_ms)
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        patient_access = context.patient_access
        encounter_access = context.encounter_access
        patient_verified = patient_access is not None and patient_access.status == ContextAccessStatus.ALLOWED
        encounter_verified = encounter_access is not None and encounter_access.status == ContextAccessStatus.ALLOWED
        final = self.authorization_service.authorize(
            principal,
            request,
            patient_access_verified=patient_verified,
            encounter_access_verified=encounter_verified,
        )
        if final.status != GatewayDecisionStatus.ALLOWED:
            reasons = tuple(final.reason_codes) or ("AUTHORIZATION_FAILED",)
            stages[auth_stage_index] = StageResult(GatewayStage.AUTHORIZATION, GatewayExecutionStatus.BLOCKED, reasons, stages[auth_stage_index].duration_ms)
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        stages[auth_stage_index] = StageResult(GatewayStage.AUTHORIZATION, GatewayExecutionStatus.COMPLETED, (), stages[auth_stage_index].duration_ms)

        timer = StageTimer(GatewayStage.PHI_PROTECTION); timer.start()
        try:
            protected = await self._protect(principal, request, context)
        except PHIDataProviderUnavailableError:
            reasons = ("PHI_PROVIDER_FAILED",)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        except PHIQueryInspectionError:
            reasons = ("PHI_QUERY_INSPECTION_FAILED",)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        except PHIPolicyError:
            reasons = ("PHI_POLICY_MISSING",)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        except (PHIValidationError, ValueError):
            reasons = ("PHI_VALIDATION_FAILED",)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        except Exception:
            reasons = ("PHI_PROTECTION_FAILED",)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        try:
            self._validate_protected_context(protected=protected, request=request, validated_context=context)
            protected_query = self._protected_query(protected)
        except Exception:
            reasons = ("PHI_VALIDATION_FAILED",)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        phi_review = protected.human_review_required
        execution_request = request.model_copy(update={"query": protected_query})
        try:
            model_input = ProtectedModelInput.from_protected_context(protected)
        except Exception:
            reasons = ("PHI_MODEL_INPUT_INVALID",)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        stages.append(timer.finish(GatewayExecutionStatus.REVIEW_REQUIRED if phi_review else GatewayExecutionStatus.COMPLETED))

        timer = StageTimer(GatewayStage.SAFETY_CLASSIFICATION); timer.start()
        try:
            safety = self.safety_service.classify(request.capability, protected_query)
        except Exception:
            reasons = ("SAFETY_CLASSIFICATION_FAILED",)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, principal=principal)
        if safety.decision in {AISafetyDecision.DENY, AISafetyDecision.ESCALATE}:
            reason = (safety.reason_code,)
            stages.append(timer.finish(GatewayExecutionStatus.BLOCKED, reason))
            return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reason, principal=principal)
        review = phi_review or safety.decision == AISafetyDecision.REVIEW_REQUIRED or safety.requires_human_review
        stages.append(timer.finish(GatewayExecutionStatus.REVIEW_REQUIRED if review else GatewayExecutionStatus.COMPLETED, (safety.reason_code,)))

        timer = StageTimer(GatewayStage.EXECUTION); timer.start()
        try:
            output = await self.executor.execute(request=execution_request, principal=principal, validated_context=context, protected_request=model_input)
        except Exception:
            reasons = ("AI_EXECUTION_FAILED",)
            stages.append(timer.finish(GatewayExecutionStatus.FAILED, reasons))
            return self._result(request, GatewayExecutionStatus.FAILED, stages, reasons, review, principal=principal)
        stages.append(timer.finish(GatewayExecutionStatus.REVIEW_REQUIRED if review else GatewayExecutionStatus.COMPLETED))
        if self.output_validator is not None:
            output_timer = StageTimer(GatewayStage.OUTPUT_VALIDATION); output_timer.start()
            allowed_source_ids: set[str] = set()
            if isinstance(protected, dict):
                allowed_source_ids = set(protected.get("allowed_source_ids", set()))
            else:
                allowed_source_ids = set(getattr(protected, "allowed_source_ids", set()))
            validation = self.output_validator.validate(raw_output=output, allowed_source_ids=allowed_source_ids, human_review_required=review)
            if validation.status.value in {"INVALID", "BLOCKED"}:
                reasons = tuple(failure.reason_code for failure in validation.failures) or ("OUTPUT_VALIDATION_FAILED",)
                stages.append(output_timer.finish(GatewayExecutionStatus.BLOCKED, reasons))
                return self._result(request, GatewayExecutionStatus.BLOCKED, stages, reasons, review, principal=principal)
            review = review or validation.status.value == "REVIEW_REQUIRED"
            output = validation.response
            stages.append(output_timer.finish(GatewayExecutionStatus.REVIEW_REQUIRED if review else GatewayExecutionStatus.COMPLETED, tuple(f.reason_code for f in validation.failures)))
        overall = GatewayExecutionStatus.REVIEW_REQUIRED if review else GatewayExecutionStatus.COMPLETED
        return self._result(request, overall, stages, (), review, output, principal)

    async def _protect(self, principal: AuthenticatedPrincipal, request: GatewayRequest, context: ValidatedRequestContext) -> ProtectedAIContext:
        protect = getattr(self.phi_service, "protect", None)
        if not callable(protect):
            raise PHIValidationError("A structured PHI protection service is required.")
        result = protect(principal=principal, request=request, validated_context=context)
        result = await result if inspect.isawaitable(result) else result
        if not isinstance(result, ProtectedAIContext):
            raise PHIValidationError("PHI protection returned an unsupported context type.")
        return result

    @staticmethod
    def _protected_query(protected: ProtectedAIContext) -> str:
        value = protected.query
        if not isinstance(value, str) or not value.strip():
            raise ValueError("PHI protection did not return an inspected query.")
        return value

    @staticmethod
    def _validate_protected_context(*, protected: ProtectedAIContext, request: GatewayRequest, validated_context: ValidatedRequestContext) -> None:
        policy = get_projection_policy(request.capability.value)
        validate_protected_context(policy=policy, context=protected)
        if protected.organization_id != validated_context.organization_id or protected.facility_id != validated_context.facility_id or protected.department_id != validated_context.department_id:
            raise PHIValidationError("Protected context scope does not match validated context.")
        if protected.capability != request.capability.value or protected.purpose != (request.purpose or "").strip():
            raise PHIValidationError("Protected context does not match the request.")
        if protected.decision != PHIHandlingDecision.ALLOWED:
            raise PHIValidationError("Protected context is not approved for inference.")

    async def orchestrate(self, *, principal: AuthenticatedPrincipal, request: GatewayRequest) -> OrchestrationResult:
        return await self.execute(principal=principal, request=request)

    async def run(self, *, principal: AuthenticatedPrincipal, request: GatewayRequest) -> OrchestrationResult:
        return await self.execute(principal=principal, request=request)
