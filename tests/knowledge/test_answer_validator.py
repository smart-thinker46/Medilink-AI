import json
import pytest

from medilink_ai.knowledge.answer_schemas import KnowledgeAnswer
from medilink_ai.knowledge.answer_validator import KnowledgeAnswerValidationError, KnowledgeAnswerValidator
from medilink_ai.knowledge.evidence_models import EvidenceBundle, EvidenceItem, EvidenceSource


def bundle():
    source = EvidenceSource("S1", "doc-1", "chunk-1", "SOP", "1.0", "SOP", "sop.md", None, 0, None, None)
    return EvidenceBundle("q", (EvidenceItem(source, "Verify identity."),), 16)


def test_validator_accepts_known_citation():
    raw = json.dumps({"answer": "Verify identity. [S1]", "status": "ANSWERED", "citations": [{"source_id": "S1", "claim": "Identity is verified."}]})
    assert KnowledgeAnswerValidator().validate(raw, bundle()).status == "ANSWERED"


def test_validator_rejects_unknown_citation():
    raw = json.dumps({"answer": "Unsupported. [S9]", "status": "ANSWERED", "citations": [{"source_id": "S9", "claim": "Unsupported."}]})
    with pytest.raises(KnowledgeAnswerValidationError):
        KnowledgeAnswerValidator().validate(raw, bundle())
