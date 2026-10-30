from pathlib import Path


def extract_text(path: Path) -> str:
    if path.suffix.lower() not in {".txt", ".md"}:
        raise ValueError(f"Unsupported text file type: {path.suffix}")
    return path.read_text(encoding="utf-8", errors="strict")
