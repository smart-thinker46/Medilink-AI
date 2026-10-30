"""Small offline embedding adapter for the CPU-only prototype.

This deterministic hashing embedder keeps semantic retrieval usable without
downloading a model. It is intentionally replaceable by a local sentence-
transformer service later; the retrieval API does not depend on its internals.
"""
from __future__ import annotations
import hashlib
import math
import re


class EmbeddingService:
    dimensions = 256

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def similarity(self, left: str, right: str) -> float:
        a, b = self.embed(left), self.embed(right)
        return max(0.0, sum(x * y for x, y in zip(a, b)))
