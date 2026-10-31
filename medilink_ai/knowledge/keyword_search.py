"""PostgreSQL full-text retrieval for exact HMIS terminology."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db_models import KnowledgeChunk, KnowledgeDocument
from .access import KnowledgeAccessContext
from .database_filters import build_authorized_knowledge_statement


@dataclass(frozen=True)
class KeywordSearchResult:
    chunk: KnowledgeChunk
    score: float


class KeywordSearchService:
    """Retrieve knowledge chunks using PostgreSQL's lexical ranking only."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        query: str,
        context: KnowledgeAccessContext,
        top_k: int = 5,
        candidate_limit: int | None = None,
    ) -> list[KeywordSearchResult]:
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")
        limit = candidate_limit or max(top_k, top_k * 5)
        if not 1 <= limit <= 250:
            raise ValueError("candidate_limit must be between 1 and 250")

        # Use the same simple configuration for indexing and querying. It is
        # predictable for clinical identifiers such as ICD-10, CBC and OPD.
        document_text = func.concat_ws(" ", KnowledgeDocument.title, KnowledgeChunk.content)
        vector = func.to_tsvector("simple", document_text)
        ts_query = func.plainto_tsquery("simple", query.strip())
        score = func.ts_rank_cd(vector, ts_query).label("score")
        statement = (
            build_authorized_knowledge_statement(context)
            .add_columns(score)
            .where(vector.op("@@")(ts_query))
            .order_by(score.desc(), KnowledgeChunk.chunk_index.asc())
            .limit(limit)
        )
        rows = self.session.execute(statement).all()
        return [KeywordSearchResult(chunk=chunk, score=float(value or 0.0)) for chunk, _document, value in rows[:top_k]]
