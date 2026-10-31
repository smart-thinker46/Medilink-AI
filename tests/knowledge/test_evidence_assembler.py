from datetime import date
from types import SimpleNamespace

from medilink_ai.knowledge.evidence_assembler import EvidenceAssembler
from medilink_ai.knowledge.hybrid_search import HybridSearchResult


def candidate(chunk_id: str, content: str):
    document = SimpleNamespace(id="doc-1", title="Registration SOP", version="2.1", document_type="SOP", source_filename="registration.md", effective_from=date.today(), effective_until=None)
    chunk = SimpleNamespace(id=chunk_id, document_id="doc-1", document=document, content=content, chunk_index=1)
    return HybridSearchResult(chunk_id, chunk, .03, 1, 1)


def test_assembler_deduplicates_and_limits_evidence():
    bundle = EvidenceAssembler(max_sources=5, max_chunk_characters=30, max_total_characters=40).assemble(
        "register patient", [candidate("a", "Same registration evidence."), candidate("b", "Same registration evidence."), candidate("c", "Another registration instruction.")]
    )
    assert len(bundle.items) == 2
    assert bundle.total_characters <= 40
    assert bundle.items[0].source.source_id == "S1"
