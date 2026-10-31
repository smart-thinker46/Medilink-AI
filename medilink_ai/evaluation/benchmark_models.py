from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import json
import os
from uuid import uuid4

from ..inference.config import OLLAMA_CHAT_MODEL, OLLAMA_TEMPERATURE
from ..knowledge.embeddings import get_embedding_service


@dataclass(frozen=True)
class BenchmarkManifest:
    benchmark_id: str
    created_at: str
    evaluation_version: str
    dataset_name: str
    dataset_version: str
    environment: str
    database_name: str
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    retrieval_strategy: str
    ranking_strategy: str
    reranker_name: str | None
    top_k: int
    candidate_limit: int
    temperature: float
    generation_enabled: bool


def database_name_from_url(url: str | None) -> str:
    if not url:
        return "unknown"
    return urlparse(url).path.strip("/") or "unknown"


def build_manifest(*, dataset_name: str, dataset_version: str, top_k: int, candidate_limit: int, generation_enabled: bool) -> BenchmarkManifest:
    embedding_backend = os.getenv("MEDILINK_EMBEDDING_BACKEND", "hashing")
    embedding_model = os.getenv("MEDILINK_EMBEDDING_MODEL", "hashing")
    embedding = get_embedding_service()
    return BenchmarkManifest(
        benchmark_id=f"benchmark-{uuid4().hex}",
        created_at=datetime.now(timezone.utc).isoformat(),
        evaluation_version="1.0",
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        environment=os.getenv("MEDILINK_ENVIRONMENT", "development"),
        database_name=database_name_from_url(os.getenv("EVALUATION_DATABASE_URL" if generation_enabled or os.getenv("MEDILINK_ENVIRONMENT") == "evaluation" else "DATABASE_URL")),
        llm_provider="ollama",
        llm_model=OLLAMA_CHAT_MODEL,
        embedding_provider=embedding_backend,
        embedding_model=embedding_model,
        embedding_dimensions=embedding.dimension,
        retrieval_strategy="hybrid",
        ranking_strategy="reciprocal-rank-fusion",
        reranker_name="local-evidence-reranker",
        top_k=top_k,
        candidate_limit=candidate_limit,
        temperature=OLLAMA_TEMPERATURE,
        generation_enabled=generation_enabled,
    )


def write_manifest(path: str | Path, manifest: BenchmarkManifest) -> None:
    Path(path).write_text(json.dumps(asdict(manifest), indent=2) + "\n", encoding="utf-8")
