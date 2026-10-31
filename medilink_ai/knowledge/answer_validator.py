from __future__ import annotations

import json

from pydantic import ValidationError

from .answer_schemas import KnowledgeAnswer
from .evidence_models import EvidenceBundle


class KnowledgeAnswerValidationError(ValueError):
    pass


class KnowledgeAnswerValidator:
    def validate(self, raw_output: str, evidence_bundle: EvidenceBundle) -> KnowledgeAnswer:
        try:
            answer = KnowledgeAnswer.model_validate(json.loads(raw_output))
        except (json.JSONDecodeError, TypeError, ValidationError) as exc:
            raise KnowledgeAnswerValidationError("The model response was not valid structured JSON.") from exc
        source_ids = {item.source.source_id for item in evidence_bundle.items}
        if answer.status == "ANSWERED" and not answer.citations:
            raise KnowledgeAnswerValidationError("Answered responses must include citations.")
        unknown = [citation.source_id for citation in answer.citations if citation.source_id not in source_ids]
        if unknown:
            raise KnowledgeAnswerValidationError("The response cited an unavailable evidence source.")
        if not evidence_bundle.items and answer.status == "ANSWERED":
            raise KnowledgeAnswerValidationError("An answer cannot be marked ANSWERED without evidence.")
        return answer
