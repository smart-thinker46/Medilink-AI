from pathlib import Path
from uuid import uuid4
from .chunking import chunk_text
from .cleaning import clean_document_text
from .extractors import extract_document_text
from .models import DocumentMetadata, KnowledgeChunk
from .schemas import DocumentMetadataRequest
from .storage.json_store import save_chunks

ALLOWED_CLASSIFICATIONS = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}


def ingest_document(
    path: Path,
    metadata_request: DocumentMetadataRequest,
    store_path: Path,
    source_filename: str | None = None,
) -> tuple[str, int, int]:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("The supplied document does not exist.")
    if metadata_request.classification not in ALLOWED_CLASSIFICATIONS:
        raise ValueError("classification must be PUBLIC, INTERNAL, CONFIDENTIAL, or RESTRICTED")
    raw = extract_document_text(path)
    cleaned = clean_document_text(raw)
    if not cleaned:
        raise ValueError("No text could be extracted. Scanned PDFs require a separately approved OCR workflow.")
    document_id = str(uuid4())
    metadata = DocumentMetadata(
        document_id=document_id,
        organization_id=metadata_request.organization_id.strip(),
        facility_id=metadata_request.facility_id.strip(),
        department_id=metadata_request.department_id,
        title=metadata_request.title.strip(),
        document_type=metadata_request.document_type.strip().upper(),
        classification=metadata_request.classification,
        version=metadata_request.version.strip(),
        allowed_roles=[value.strip().lower() for value in metadata_request.allowed_roles if value.strip()],
        allowed_users=[value.strip() for value in metadata_request.allowed_users if value.strip()],
        effective_from=metadata_request.effective_from,
        effective_until=metadata_request.effective_until,
        source_filename=(source_filename or path.name),
    )
    text_chunks = chunk_text(cleaned)
    chunks = [KnowledgeChunk(f"{document_id}:{part.index}", document_id, part.index, part.text, metadata) for part in text_chunks]
    save_chunks(chunks, store_path)
    return document_id, len(cleaned), len(chunks)
