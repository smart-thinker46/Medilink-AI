from pathlib import Path
def extract_pdf_text(path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, received: {path.suffix}")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF support requires the pypdf dependency. Install requirements.txt.") from exc
    pages = [(page.extract_text() or "") for page in PdfReader(str(path)).pages]
    return "\n\n".join(page for page in pages if page)
