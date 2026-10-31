"""Initialize the isolated evaluation knowledge schema."""
from sqlalchemy import text

from ..db.base import Base
from ..knowledge import db_models  # noqa: F401
from .db import create_evaluation_engine


def initialize_evaluation_database() -> None:
    engine = create_evaluation_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=connection)


if __name__ == "__main__":
    initialize_evaluation_database()
    print("Medilink AI evaluation database initialized.")
