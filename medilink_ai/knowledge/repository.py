"""Persistence boundary for the PostgreSQL knowledge store."""
from __future__ import annotations

from sqlalchemy.orm import Session

from .db_models import KnowledgeChunk, KnowledgeDocument


class KnowledgeRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_document(self, document: KnowledgeDocument) -> KnowledgeDocument:
        self.session.add(document)
        self.session.flush()
        return document

    def add_chunk(self, chunk: KnowledgeChunk) -> KnowledgeChunk:
        self.session.add(chunk)
        self.session.flush()
        return chunk

    def commit(self) -> None:
        self.session.commit()
