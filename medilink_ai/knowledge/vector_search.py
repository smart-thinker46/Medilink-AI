"""Semantic similarity search over stored pgvector embeddings."""
from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy.orm import Session

from .db_models import KnowledgeChunk
from .embeddings import get_embedding_service
from .access import KnowledgeAccessContext
from .database_filters import build_authorized_knowledge_statement


@dataclass
class VectorSearchResult:
    chunk: KnowledgeChunk
    similarity: float


class VectorSearchService:
    def __init__(self, session: Session):
        self.session = session
        self.embedding_service = get_embedding_service()

    def search(self, query: str, context: KnowledgeAccessContext, top_k: int = 5, candidate_limit: int | None = None) -> list[VectorSearchResult]:
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")
        limit = candidate_limit or max(top_k, top_k * 5)
        if not 1 <= limit <= 250:
            raise ValueError("candidate_limit must be between 1 and 250")
        vector = self.embedding_service.embed_text(query)
        distance = KnowledgeChunk.embedding.cosine_distance(vector)
        statement = (
            build_authorized_knowledge_statement(context)
            .add_columns((1 - distance).label("similarity"))
            .where(KnowledgeChunk.embedding.is_not(None))
            .order_by(distance.asc())
            .limit(limit)
        )
        rows = self.session.execute(statement).all()
        return [VectorSearchResult(chunk=chunk, similarity=float(similarity)) for chunk, _document, similarity in rows[:top_k]]
