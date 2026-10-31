"""Generate and persist embeddings for prepared knowledge chunks."""
from __future__ import annotations

from uuid import uuid4
from sqlalchemy.orm import Session

from .db_models import KnowledgeChunk, KnowledgeDocument
from .embeddings import get_embedding_service
from .repository import KnowledgeRepository


class KnowledgeIngestionService:
    def __init__(self, session: Session):
        self.repository = KnowledgeRepository(session)
        self.embedding_service = get_embedding_service()

    def add_document_with_chunks(self, document: KnowledgeDocument, contents: list[str]) -> KnowledgeDocument:
        """Store a document and embed each already-cleaned chunk exactly once."""
        if not contents or any(not str(content).strip() for content in contents):
            raise ValueError("contents must contain at least one non-empty chunk")
        self.repository.add_document(document)
        vectors = self.embedding_service.embed_many([str(content).strip() for content in contents])
        for index, (content, vector) in enumerate(zip(contents, vectors)):
            self.repository.add_chunk(KnowledgeChunk(
                id=f"{document.id}:{index}:{uuid4().hex[:8]}",
                document_id=document.id,
                chunk_index=index,
                content=str(content).strip(),
                embedding=vector,
            ))
        self.repository.commit()
        return document
