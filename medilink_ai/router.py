"""Routes a governed request to deterministic logic, RAG, or local inference."""
from __future__ import annotations

from .contracts import AIRequest, Priority, RouteDecision, TaskType


def route(request: AIRequest) -> RouteDecision:
    if request.task_type is TaskType.QUESTION_ANSWERING:
        return RouteDecision("rag", request.task_type, Priority.OPERATIONAL, requires_rag=True)
    if request.task_type in {TaskType.CLASSIFICATION, TaskType.FORECASTING, TaskType.ANOMALY_DETECTION}:
        return RouteDecision("deterministic", request.task_type, Priority.ANALYTICS)
    if request.task_type is TaskType.DOCUMENT_GENERATION:
        return RouteDecision("local_llm", request.task_type, Priority.CLINICAL_DOCUMENTATION, safety_level="CLINICAL_DRAFT")
    return RouteDecision("local_llm", request.task_type, Priority.PATIENT_SUMMARY, safety_level="CLINICAL_EVIDENCE")
