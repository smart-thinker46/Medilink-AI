from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import AICapability


class GatewayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID = Field(default_factory=uuid4)
    capability: AICapability
    module: str = Field(min_length=2, max_length=100)
    facility_id: str = Field(min_length=2, max_length=100)
    department_id: str | None = Field(default=None, max_length=100)
    patient_id: str | None = Field(default=None, max_length=100)
    encounter_id: str | None = Field(default=None, max_length=100)
    query: str | None = Field(default=None, min_length=1, max_length=12000)
    purpose: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def encounter_requires_patient(self):
        if self.encounter_id and not self.patient_id:
            raise ValueError("encounter_id requires patient_id")
        if self.capability == AICapability.PATIENT_SUMMARY and not self.patient_id:
            raise ValueError("patient.summary requires patient_id")
        return self
