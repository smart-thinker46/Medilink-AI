from __future__ import annotations

import hashlib
import re

from .evidence_models import EvidenceBundle, EvidenceItem, EvidenceSource
from .hybrid_search import HybridSearchResult


class EvidenceAssembler:
    def __init__(self, max_sources: int = 5, max_chunk_characters: int = 3000, max_total_characters: int = 12000) -> None:
        if min(max_sources, max_chunk_characters, max_total_characters) <= 0:
            raise ValueError("evidence limits must be positive")
        self.max_sources = max_sources
        self.max_chunk_characters = max_chunk_characters
        self.max_total_characters = max_total_characters

    def assemble(self, query: str, candidates: list[HybridSearchResult]) -> EvidenceBundle:
        items: list[EvidenceItem] = []
        seen: set[str] = set()
        total = 0
        for index, candidate in enumerate(candidates[: self.max_sources], start=1):
            chunk = candidate.chunk
            content = str(getattr(chunk, "content", "")).strip()
            if not content:
                continue
            normalized = re.sub(r"\s+", " ", content).strip().lower()
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            if digest in seen:
                continue
            remaining = self.max_total_characters - total
            if remaining <= 0:
                break
            content = content[: min(self.max_chunk_characters, remaining)].strip()
            if not content:
                continue
            document = getattr(chunk, "document", None)
            section_match = re.search(r"(?m)^\s*#+\s*(.+?)\s*$", content)
            source = EvidenceSource(
                source_id=f"S{index}",
                document_id=str(getattr(document, "id", getattr(chunk, "document_id", ""))),
                chunk_id=str(getattr(chunk, "id", candidate.chunk_id)),
                title=str(getattr(document, "title", "Untitled")),
                version=str(getattr(document, "version", "unversioned")),
                document_type=str(getattr(document, "document_type", "")),
                source_filename=str(getattr(document, "source_filename", "")),
                section=section_match.group(1).strip() if section_match else None,
                chunk_index=int(getattr(chunk, "chunk_index", 0)),
                effective_from=getattr(document, "effective_from", None),
                effective_until=getattr(document, "effective_until", None),
            )
            items.append(EvidenceItem(source, content))
            seen.add(digest)
            total += len(content)
        return EvidenceBundle(query=query, items=tuple(items), total_characters=total)
