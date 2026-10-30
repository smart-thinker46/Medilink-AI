from dataclasses import dataclass, field
from datetime import date


@dataclass
class DocumentMetadata:
    document_id: str
    organization_id: str
    facility_id: str
    department_id: str | None
    title: str
    document_type: str
    classification: str
    version: str
    allowed_roles: list[str] = field(default_factory=list)
    allowed_users: list[str] = field(default_factory=list)
    effective_from: date | None = None
    effective_until: date | None = None
    source_filename: str = ""


@dataclass
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    metadata: DocumentMetadata
