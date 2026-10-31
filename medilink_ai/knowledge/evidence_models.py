from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EvidenceSource:
    source_id: str
    document_id: str
    chunk_id: str
    title: str
    version: str
    document_type: str
    source_filename: str
    section: str | None
    chunk_index: int
    effective_from: date | None
    effective_until: date | None


@dataclass(frozen=True)
class EvidenceItem:
    source: EvidenceSource
    content: str


@dataclass(frozen=True)
class EvidenceBundle:
    query: str
    items: tuple[EvidenceItem, ...]
    total_characters: int
