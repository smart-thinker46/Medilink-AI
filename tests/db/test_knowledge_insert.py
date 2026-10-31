import os
from datetime import date
from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("psycopg")
pytest.importorskip("pgvector")

if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL is not configured", allow_module_level=True)

from medilink_ai.db.session import get_session_factory
from medilink_ai.knowledge.db_models import KnowledgeDocument


def test_insert_knowledge_document():
    session = get_session_factory()()
    document = KnowledgeDocument(
        id=str(uuid4()), organization_id="test-org", facility_id="test-facility",
        department_id="administration", title="Test Patient Registration Policy",
        document_type="POLICY", classification="INTERNAL", version="1.0",
        source_filename="test-registration-policy.pdf", content_sha256="0" * 64,
        allowed_roles=["registration_officer"], allowed_users=[], effective_from=date(2026, 1, 1),
    )
    try:
        session.add(document)
        session.commit()
        assert document.id
    finally:
        session.delete(document)
        session.commit()
        session.close()
