from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

AnswerStatus = Literal["ANSWERED", "INSUFFICIENT_EVIDENCE", "CONFLICTING_EVIDENCE", "REVIEW_REQUIRED"]


class AnswerCitation(BaseModel):
    source_id: str = Field(min_length=2, max_length=20)
    claim: str = Field(min_length=1, max_length=1000)


class KnowledgeAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=10000)
    status: AnswerStatus
    citations: list[AnswerCitation] = Field(default_factory=list, max_length=10)
    limitations: list[str] = Field(default_factory=list, max_length=10)
    human_review_required: bool = True
