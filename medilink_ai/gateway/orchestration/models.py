from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GatewayStage(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    CONTEXT_VALIDATION = "CONTEXT_VALIDATION"
    PHI_PROTECTION = "PHI_PROTECTION"
    SAFETY_CLASSIFICATION = "SAFETY_CLASSIFICATION"
    EXECUTION = "EXECUTION"
    OUTPUT_VALIDATION = "OUTPUT_VALIDATION"


class GatewayExecutionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class StageResult:
    stage: GatewayStage
    status: GatewayExecutionStatus
    reason_codes: tuple[str, ...] = ()
    duration_ms: float = 0.0


@dataclass(frozen=True)
class OrchestrationResult:
    request_id: str
    status: GatewayExecutionStatus
    stages: tuple[StageResult, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = ()
    human_review_required: bool = False
    output: Any = None

    @property
    def stage_results(self) -> tuple[StageResult, ...]:
        return self.stages
