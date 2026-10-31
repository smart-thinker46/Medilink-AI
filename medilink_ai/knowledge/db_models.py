"""SQLAlchemy mappings for the persistent knowledge store.

These mappings intentionally match ``sql/001_knowledge_pgvector.sql``. The
JSON store remains the development fallback; importing this module does not
open a database connection.
"""
from __future__ import annotations

from datetime import date, datetime

try:
    from pgvector.sqlalchemy import Vector
    from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, func
    from sqlalchemy.dialects.postgresql import JSONB, UUID
    from sqlalchemy.orm import Mapped, mapped_column, relationship
    from ..db.base import Base
except ImportError as exc:  # pragma: no cover - used only before optional DB install
    raise RuntimeError("Install database dependencies from requirements.txt to use ORM models.") from exc

EMBEDDING_DIMENSION = 256


class KnowledgeDocument(Base):
    __tablename__ = "ai_knowledge_documents"

    id: Mapped[str] = mapped_column("document_id", UUID(as_uuid=False), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    facility_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    department_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    classification: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    allowed_roles: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    allowed_users: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    __tablename__ = "ai_knowledge_chunks"

    id: Mapped[str] = mapped_column("chunk_id", String(200), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("ai_knowledge_documents.document_id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")


Index("ai_knowledge_chunks_document_idx", KnowledgeChunk.document_id)
Index(
    "ai_knowledge_chunks_embedding_hnsw_idx",
    KnowledgeChunk.embedding,
    postgresql_using="hnsw",
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
