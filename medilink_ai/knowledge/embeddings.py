"""Replaceable local embedding service for the CPU-only prototype.

This deterministic hashing embedder keeps semantic retrieval usable without
downloading a model. It is intentionally replaceable by a local sentence-
transformer service later; the retrieval API does not depend on its internals.
"""
from __future__ import annotations
import hashlib
import math
import re
from abc import ABC, abstractmethod
from functools import lru_cache
import os


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def similarity(self, left: str, right: str) -> float:
        a, b = self.embed_text(left), self.embed_text(right)
        return max(0.0, sum(x * y for x, y in zip(a, b)))


class HashingEmbeddingService(EmbeddingProvider):
    dimensions = int(os.getenv("MEDILINK_EMBEDDING_DIMENSION", "256"))

    @property
    def dimension(self) -> int:
        return self.dimensions

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    # Backwards-compatible name used by the retrieval layer and pgvector adapter.
    embed = embed_text


class SentenceTransformerEmbeddingService(EmbeddingProvider):
    def __init__(self, model_name: str, expected_dimension: int):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Sentence Transformers is not installed. Install requirements.txt or use "
                "MEDILINK_EMBEDDING_BACKEND=hashing."
            ) from exc
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device="cpu")
        actual_dimension = self.model.get_sentence_embedding_dimension()
        if actual_dimension != expected_dimension:
            raise RuntimeError(
                f"Embedding dimension mismatch: configured={expected_dimension}, model={actual_dimension}."
            )
        self._dimension = actual_dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        values = self.model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
        return [float(value) for value in values.tolist()]


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingProvider:
    backend = os.getenv("MEDILINK_EMBEDDING_BACKEND", "hashing").strip().lower()
    dimension = int(os.getenv("MEDILINK_EMBEDDING_DIMENSION", "256"))
    if backend in {"sentence-transformers", "sentence_transformers", "minilm"}:
        return SentenceTransformerEmbeddingService(
            os.getenv("MEDILINK_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            dimension,
        )
    if backend != "hashing":
        raise ValueError("MEDILINK_EMBEDDING_BACKEND must be 'hashing' or 'sentence-transformers'.")
    return HashingEmbeddingService()


# Existing callers can continue to instantiate EmbeddingService().
EmbeddingService = HashingEmbeddingService
