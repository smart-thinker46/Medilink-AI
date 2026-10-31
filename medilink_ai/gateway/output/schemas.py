from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GatewayCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(min_length=1, max_length=100)
    claim: str = Field(min_length=1, max_length=2000)


class GatewayAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=20000)
    status: str = Field(min_length=1, max_length=50)
    citations: list[GatewayCitation] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)
    human_review_required: bool = False
