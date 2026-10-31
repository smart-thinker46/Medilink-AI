import os

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("psycopg")
pytest.importorskip("pgvector")

if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL is not configured", allow_module_level=True)

from sqlalchemy import inspect
from medilink_ai.db.session import get_engine


def test_knowledge_tables_exist():
    tables = set(inspect(get_engine()).get_table_names())
    assert {"ai_knowledge_documents", "ai_knowledge_chunks"}.issubset(tables)


def test_knowledge_chunks_has_embedding():
    columns = inspect(get_engine()).get_columns("ai_knowledge_chunks")
    assert "embedding" in {column["name"] for column in columns}
