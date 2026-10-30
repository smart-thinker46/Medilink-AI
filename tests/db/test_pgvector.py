import os

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("psycopg")

if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL is not configured", allow_module_level=True)

from sqlalchemy import text
from medilink_ai.db.session import get_engine


def test_pgvector_extension():
    with get_engine().connect() as connection:
        extension = connection.execute(text(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        )).scalar_one_or_none()
        assert extension == "vector"
