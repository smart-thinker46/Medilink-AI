from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..knowledge.db_models import KnowledgeDocument
from ..knowledge.vector_ingestion import KnowledgeIngestionService

EVALUATION_NAMESPACE = UUID("4b3f1c8c-ea69-5b4e-a7ad-1c2c2e4f72a3")
STABLE_DOCUMENT_IDS = {
    "EVAL-DOC-POS-001": "10000000-0000-4000-8000-000000000001",
    "EVAL-DOC-BILL-001": "10000000-0000-4000-8000-000000000002",
    "EVAL-DOC-LAB-001": "10000000-0000-4000-8000-000000000003",
    "EVAL-DOC-CLINICAL-001": "10000000-0000-4000-8000-000000000004",
    "EVAL-DOC-OTHER-FACILITY-001": "10000000-0000-4000-8000-000000000005",
}
LEGACY_DOCUMENT_IDS = {value: key for key, value in STABLE_DOCUMENT_IDS.items()}


def load_controlled_fixtures(session: Session, path: str | Path) -> int:
    """Upsert synthetic evaluation documents without deleting other records."""
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list):
        raise ValueError("Fixture file must contain a document object or an array of documents.")
    loaded = 0
    ingestion = KnowledgeIngestionService(session)
    for raw in records:
        raw_document_id = str(raw["document_id"])
        raw_document_id = STABLE_DOCUMENT_IDS.get(raw_document_id, raw_document_id)
        try:
            document_id = str(UUID(raw_document_id))
        except ValueError:
            document_id = str(uuid5(EVALUATION_NAMESPACE, raw_document_id))
        if session.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)):
            continue
        document = KnowledgeDocument(
            id=document_id,
            organization_id=raw["organization_id"],
            facility_id=raw["facility_id"],
            department_id=raw.get("department_id"),
            title=raw["title"],
            document_type=raw["document_type"],
            classification=raw["classification"],
            version=raw["version"],
            allowed_roles=[str(value).lower() for value in raw.get("allowed_roles", [])],
            allowed_users=list(raw.get("allowed_users", [])),
            effective_from=date.fromisoformat(raw["effective_from"]) if raw.get("effective_from") else None,
            effective_until=date.fromisoformat(raw["effective_until"]) if raw.get("effective_until") else None,
            source_filename=raw["source_filename"],
            content_sha256=f"evaluation:{raw['document_id']}",
        )
        ingestion.add_document_with_chunks(document, [chunk["content"] for chunk in raw.get("chunks", [])])
        loaded += 1
    return loaded
