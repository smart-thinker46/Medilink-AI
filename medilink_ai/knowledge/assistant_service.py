from __future__ import annotations

from sqlalchemy.orm import Session

from ..inference.config import OLLAMA_CHAT_MODEL, OLLAMA_NUM_PREDICT, OLLAMA_TEMPERATURE
from ..inference.models import GenerationRequest
from ..inference.service import get_inference_provider
from ..prompts.knowledge_assistant import KNOWLEDGE_ASSISTANT_SYSTEM_PROMPT, build_knowledge_user_prompt
from .access import KnowledgeAccessContext
from .answer_safety import KnowledgeAnswerSafety
from .answer_schemas import KnowledgeAnswer
from .answer_validator import KnowledgeAnswerValidationError, KnowledgeAnswerValidator
from .evidence_pipeline import KnowledgeEvidencePipeline
from ..safety import check_request


class HospitalKnowledgeAssistant:
    def __init__(self, session: Session) -> None:
        self.evidence_pipeline = KnowledgeEvidencePipeline(session)
        self.validator = KnowledgeAnswerValidator()
        self.safety = KnowledgeAnswerSafety()
        self.provider = get_inference_provider()

    async def ask(self, query: str, context: KnowledgeAccessContext) -> KnowledgeAnswer:
        refusal = check_request(query)
        if refusal:
            return KnowledgeAnswer(answer=refusal, status="REVIEW_REQUIRED", limitations=["This request requires an authorized human decision."], human_review_required=True)
        evidence = self.evidence_pipeline.search(query, context).evidence
        if not evidence.items:
            return KnowledgeAnswer(
                answer="I could not find sufficient information in the authorized Medilink knowledge sources to answer this question reliably.",
                status="INSUFFICIENT_EVIDENCE", limitations=["No authorized evidence matched the question."], human_review_required=False,
            )
        request = GenerationRequest(
            system_prompt=KNOWLEDGE_ASSISTANT_SYSTEM_PROMPT,
            user_prompt=build_knowledge_user_prompt(query, evidence),
            model=OLLAMA_CHAT_MODEL,
            temperature=OLLAMA_TEMPERATURE,
            max_tokens=OLLAMA_NUM_PREDICT,
            metadata={"source_ids": [item.source.source_id for item in evidence.items]},
        )
        try:
            response = await self.provider.generate(request)
        except Exception:
            return self._grounded_fallback(evidence)
        try:
            answer = self.validator.validate(response.content, evidence)
        except KnowledgeAnswerValidationError:
            return self._grounded_fallback(evidence)
        return self.safety.validate(answer)

    @staticmethod
    def _grounded_fallback(evidence) -> KnowledgeAnswer:
        """Return a safe, citation-bearing answer when local generation is unavailable.

        This keeps retrieval useful on small/offline models without inventing content:
        the response is composed solely from the first authorized evidence item.
        """
        items = evidence.items[:2]
        excerpts = " ".join(
            f"According to {item.source.title} (version {item.source.version}), {item.content} [{item.source.source_id}]"
            for item in items
        )
        return KnowledgeAnswer(
            answer=excerpts,
            status="ANSWERED",
            citations=[{"source_id": item.source.source_id, "claim": item.content[:1000]} for item in items],
            limitations=["This response was assembled from the authorized source because the local model response was unavailable or invalid."],
            human_review_required=True,
        )
