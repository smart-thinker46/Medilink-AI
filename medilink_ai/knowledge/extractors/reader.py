from pathlib import Path
from .pdf import extract_pdf_text
from .text import extract_text


def extract_document_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Document does not exist: {path.name}")
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    if path.suffix.lower() in {".txt", ".md"}:
        return extract_text(path)
    raise ValueError(f"Unsupported document type: {path.suffix.lower()}")
