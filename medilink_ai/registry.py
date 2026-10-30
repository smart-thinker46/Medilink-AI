"""Approved local model and capability registry.

Only entries marked APPROVED/PILOT may be routed by the gateway.  This is a
small file-backed baseline; production deployments should persist the same
fields in the dedicated AI registry database proposed by Medilink governance.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ModelRecord:
    model_id: str
    name: str
    model_type: str
    version: str
    runtime: str
    hardware: str
    status: str
    approved_for: tuple[str, ...]


MODELS = (
    ModelRecord("MED-LLM-LOCAL", "Medilink Local Assistant", "language", "0.1", "OpenAI-compatible local runtime", "CPU", "PILOT", ("clinical_summary", "note_draft", "knowledge")),
    ModelRecord("MED-RAG-BM25", "Medilink Knowledge Retrieval", "retrieval", "0.1", "Built-in BM25", "CPU", "APPROVED", ("knowledge",)),
    ModelRecord("MED-ANALYTICS-DET", "Medilink Deterministic Analytics", "analytics", "0.1", "Built-in", "CPU", "APPROVED", ("duplicates", "queue_forecast", "revenue_leakage", "feedback_themes")),
)

CAPABILITIES = (
    {"id": "clinical_summary", "label": "Patient clinical summary", "domain": "clinical", "mode": "AI insight", "human_review": True},
    {"id": "note_draft", "label": "Clinical documentation draft", "domain": "clinical", "mode": "AI-assisted draft", "human_review": True},
    {"id": "knowledge", "label": "Hospital knowledge assistant", "domain": "enterprise", "mode": "AI insight", "human_review": False},
    {"id": "duplicates", "label": "Duplicate patient review", "domain": "registration", "mode": "deterministic flag", "human_review": True},
    {"id": "queue_forecast", "label": "Queue intelligence", "domain": "operations", "mode": "deterministic forecast", "human_review": True},
    {"id": "revenue_leakage", "label": "Revenue leakage review", "domain": "financial", "mode": "deterministic flag", "human_review": True},
    {"id": "feedback_themes", "label": "Patient feedback themes", "domain": "experience", "mode": "deterministic classification", "human_review": True},
)


def platform_registry() -> dict:
    return {"models": [asdict(model) for model in MODELS], "capabilities": list(CAPABILITIES), "write_access": False}
