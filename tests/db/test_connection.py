import os

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("psycopg")

if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL is not configured", allow_module_level=True)

from sqlalchemy import text
from medilink_ai.db.session import get_engine


def test_database_connection():
    with get_engine().connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
