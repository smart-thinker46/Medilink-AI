from __future__ import annotations

from time import perf_counter

from .models import GatewayExecutionStatus, GatewayStage, StageResult


class StageTimer:
    def __init__(self, stage: GatewayStage):
        self.stage = stage
        self.started_at = 0.0

    def start(self) -> None:
        self.started_at = perf_counter()

    def finish(self, status: GatewayExecutionStatus, reason_codes: tuple[str, ...] = ()) -> StageResult:
        duration_ms = (perf_counter() - self.started_at) * 1000 if self.started_at else 0.0
        return StageResult(self.stage, status, reason_codes, duration_ms)
