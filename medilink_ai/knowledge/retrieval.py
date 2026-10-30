import json
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from .access import KnowledgeAccessContext
from .authorization import is_chunk_authorized
from .models import DocumentMetadata, KnowledgeChunk
from .embeddings import EmbeddingService


@dataclass
class RetrievalResult:
    chunk: KnowledgeChunk
    score: float


def _load_chunks(store_path: str | Path) -> list[KnowledgeChunk]:
    path = Path(store_path)
    if not path.exists():
        return []
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    chunks = []
    for row in records if isinstance(records, list) else []:
        data = row.get("metadata") or {}
        try:
            metadata = DocumentMetadata(
                document_id=str(data.get("document_id", row.get("document_id", ""))), organization_id=str(data.get("organization_id", "")),
                facility_id=str(data.get("facility_id", "")), department_id=data.get("department_id"), title=str(data.get("title", "Untitled")),
                document_type=str(data.get("document_type", "")), classification=str(data.get("classification", "INTERNAL")), version=str(data.get("version", "unversioned")),
                allowed_roles=list(data.get("allowed_roles") or []), allowed_users=list(data.get("allowed_users") or []),
                effective_from=date.fromisoformat(data["effective_from"]) if data.get("effective_from") else None,
                effective_until=date.fromisoformat(data["effective_until"]) if data.get("effective_until") else None, source_filename=str(data.get("source_filename", "")),
            )
        except (TypeError, ValueError):
            continue
        text = str(row.get("text") or "").strip()
        if text:
            chunks.append(KnowledgeChunk(str(row.get("chunk_id", "")), metadata.document_id, int(row.get("chunk_index", 0)), text, metadata))
    return chunks


def _score_chunk(query: str, chunk: KnowledgeChunk) -> float:
    query_tokens = re.findall(r"\w+", query.lower())
    tokens = re.findall(r"\w+", chunk.text.lower())
    if not query_tokens or not tokens:
        return 0.0
    counts = {token: tokens.count(token) for token in set(tokens)}
    score = sum(min(counts.get(token, 0), 3) for token in query_tokens)
    title_tokens = set(re.findall(r"\w+", chunk.metadata.title.lower()))
    score += sum(0.5 for token in query_tokens if token in title_tokens)
    keyword_score = score / math.sqrt(len(tokens))
    semantic_score = EmbeddingService().similarity(query, chunk.text)
    return (0.65 * keyword_score) + (0.35 * semantic_score)


def retrieve(query: str, context: KnowledgeAccessContext, store_path: str | Path, top_k: int = 4) -> list[RetrievalResult]:
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10")
    results = [RetrievalResult(chunk, _score_chunk(query, chunk)) for chunk in _load_chunks(store_path) if is_chunk_authorized(chunk, context)]
    return sorted((result for result in results if result.score > 0), key=lambda result: result.score, reverse=True)[:top_k]
