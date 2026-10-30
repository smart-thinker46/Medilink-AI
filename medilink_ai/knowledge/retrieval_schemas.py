from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)


class KnowledgeSource(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    version: str
    source_filename: str
    chunk_index: int
    score: float


class KnowledgeSearchResponse(BaseModel):
    status: str
    query: str
    results: list[KnowledgeSource]
