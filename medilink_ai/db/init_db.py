"""Initialize the persistent AI knowledge schema."""
from sqlalchemy import text

from .base import Base
from .session import get_engine
from ..knowledge.db_models import KnowledgeChunk, KnowledgeDocument  # noqa: F401
from ..gateway.audit import db_models as gateway_audit_models  # noqa: F401


def initialize_database() -> None:
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=connection)


if __name__ == "__main__":
    initialize_database()
    print("Medilink AI knowledge database initialized.")
