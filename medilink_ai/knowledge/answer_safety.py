from .answer_schemas import KnowledgeAnswer

HIGH_RISK_TERMS = (
    "i authorize discharge", "i approve the transfusion", "i prescribe",
    "administer this medication immediately", "i approve surgery",
    "i authorize the patient transfer", "i approve the refund", "change the patient's balance",
)


class KnowledgeAnswerSafety:
    def validate(self, answer: KnowledgeAnswer) -> KnowledgeAnswer:
        normalized = answer.answer.lower()
        if any(term in normalized for term in HIGH_RISK_TERMS):
            answer.human_review_required = True
            if answer.status == "ANSWERED":
                answer.status = "REVIEW_REQUIRED"
        return answer
