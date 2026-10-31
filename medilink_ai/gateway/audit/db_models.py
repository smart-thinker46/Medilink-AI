from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from ...db.base import Base


class GatewayAuditEventRecord(Base):
    __tablename__ = "gateway_audit_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    facility_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    department_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    module: Mapped[str | None] = mapped_column(String(100), nullable=True)
    capability: Mapped[str | None] = mapped_column(String(100), nullable=True)
    purpose_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    patient_ref_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    encounter_ref_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    evidence_document_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_chunk_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
