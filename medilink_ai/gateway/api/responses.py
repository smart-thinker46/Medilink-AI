from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GatewayStageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage: str
    status: str
    reason_codes: list[str] = Field(default_factory=list)
    duration_ms: float | None = None


class AIExecuteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    status: str
    capability: str
    response: Any | None = None
    human_review_required: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    stages: list[GatewayStageResponse] = Field(default_factory=list)
