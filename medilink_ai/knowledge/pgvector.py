"""Optional PostgreSQL/pgvector knowledge-store adapter.

The adapter is deliberately dependency-injected: the AI service never opens a
database connection by itself. A deployment supplies a trusted connection
factory (normally using the HMIS DATABASE_URL) after applying the SQL schema.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from .access import KnowledgeAccessContext
from .authorization import is_chunk_authorized
from .embeddings import EmbeddingProvider, get_embedding_service
from .models import DocumentMetadata, KnowledgeChunk


class PostgresKnowledgeStore:
    def __init__(self, connection_factory: Callable[[], object], embedder: EmbeddingProvider | None = None):
        self.connection_factory = connection_factory
        self.embedder = embedder or get_embedding_service()

    @staticmethod
    def _vector(values: Iterable[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in values) + "]"

    def search(self, query: str, context: KnowledgeAccessContext, top_k: int = 4) -> list[tuple[float, KnowledgeChunk]]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10")
        sql = """
          SELECT c.chunk_id, c.document_id, c.chunk_index, c.content,
                 d.organization_id, d.facility_id, d.department_id, d.title,
                 d.document_type, d.classification, d.version,
                 d.allowed_roles, d.allowed_users, d.effective_from,
                 d.effective_until, d.source_filename,
                 1 - (c.embedding <=> %s::vector) AS score
            FROM ai_knowledge_chunks c
            JOIN ai_knowledge_documents d ON d.document_id = c.document_id
           WHERE d.organization_id = %s AND d.facility_id = %s
             AND (d.department_id IS NULL OR d.department_id = %s)
             AND (d.effective_from IS NULL OR d.effective_from <= CURRENT_DATE)
             AND (d.effective_until IS NULL OR d.effective_until >= CURRENT_DATE)
             AND (d.allowed_roles = '[]'::jsonb OR d.allowed_roles ?| %s)
             AND (d.allowed_users = '[]'::jsonb OR d.allowed_users ? %s)
           ORDER BY c.embedding <=> %s::vector
           LIMIT %s
        """
        vector = self._vector(self.embedder.embed(query))
        roles = list(context.roles) or ["__none__"]
        with self.connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (vector, context.organization_id, context.facility_id,
                                     context.department_id, roles, context.user_id, vector, top_k))
                rows = cursor.fetchall()
        results = []
        for row in rows:
            (chunk_id, document_id, chunk_index, content, organization_id, facility_id,
             department_id, title, document_type, classification, version,
             allowed_roles, allowed_users, effective_from, effective_until,
             source_filename, score) = row
            metadata = DocumentMetadata(
                document_id=str(document_id), organization_id=organization_id,
                facility_id=facility_id, department_id=department_id, title=title,
                document_type=document_type, classification=classification,
                version=version, allowed_roles=list(allowed_roles or []),
                allowed_users=list(allowed_users or []),
                effective_from=effective_from, effective_until=effective_until,
                source_filename=source_filename,
            )
            chunk = KnowledgeChunk(str(chunk_id), str(document_id), chunk_index, content, metadata)
            if is_chunk_authorized(chunk, context):
                results.append((float(score), chunk))
        return results
