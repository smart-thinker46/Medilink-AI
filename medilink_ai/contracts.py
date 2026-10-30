"""Stable AI platform contracts shared by all Medilink AI capabilities."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class TaskType(StrEnum):
    SUMMARY = "SUMMARY"
    QUESTION_ANSWERING = "QUESTION_ANSWERING"
    DOCUMENT_GENERATION = "DOCUMENT_GENERATION"
    CLASSIFICATION = "CLASSIFICATION"
    FORECASTING = "FORECASTING"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"


class Priority(StrEnum):
    CLINICAL_SAFETY = "CLINICAL_SAFETY"
    CLINICAL_DOCUMENTATION = "CLINICAL_DOCUMENTATION"
    PATIENT_SUMMARY = "PATIENT_SUMMARY"
    OPERATIONAL = "OPERATIONAL"
    ANALYTICS = "ANALYTICS"


@dataclass(frozen=True)
class AIRequest:
    request_id: str
    user_id: str
    facility_id: str | None
    module_code: str
    task_type: TaskType
    priority: Priority
    patient_id: str | None = None
    encounter_id: str | None = None
    input: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    handler: str  # local_llm | rag | deterministic
    task_type: TaskType
    priority: Priority
    requires_rag: bool = False
    safety_level: str = "STANDARD"

    def dict(self) -> dict[str, Any]:
        return asdict(self)
