from datetime import date

from medilink_ai.knowledge.evidence_models import EvidenceBundle, EvidenceItem, EvidenceSource
from medilink_ai.prompts.knowledge_assistant import build_knowledge_user_prompt


def test_prompt_contains_question_and_source_boundary():
    source = EvidenceSource("S1", "doc-1", "chunk-1", "Registration SOP", "1.0", "SOP", "registration.md", "Register", 0, date.today(), None)
    prompt = build_knowledge_user_prompt("How do I register a patient?", EvidenceBundle("q", (EvidenceItem(source, "Verify identity before saving."),), 31))
    assert "How do I register a patient?" in prompt
    assert "S1" in prompt
    assert "Verify identity" in prompt
