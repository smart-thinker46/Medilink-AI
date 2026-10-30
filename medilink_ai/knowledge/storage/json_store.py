import json
from dataclasses import asdict
from pathlib import Path
from ..models import KnowledgeChunk


def save_chunks(chunks: list[KnowledgeChunk], store_path: Path) -> None:
    store_path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if store_path.exists():
        try:
            existing = json.loads(store_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
    document_ids = {chunk.document_id for chunk in chunks}
    existing = [row for row in existing if row.get("document_id") not in document_ids]
    payload = existing + [asdict(chunk) for chunk in chunks]
    temporary = store_path.with_suffix(store_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temporary.replace(store_path)
