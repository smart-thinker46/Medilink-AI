from __future__ import annotations

from pydantic import BaseModel, Field
from .answer_schemas import AnswerCitation, AnswerStatus


class KnowledgeAssistantRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class KnowledgeAssistantResponse(BaseModel):
    answer: str
    status: AnswerStatus
    citations: list[AnswerCitation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    human_review_required: bool = True
