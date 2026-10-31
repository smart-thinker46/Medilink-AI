from __future__ import annotations

import re

from .hybrid_search import HybridSearchResult
from .reranker_base import EvidenceReranker


def extract_tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9][a-zA-Z0-9._/-]*", text.lower())


class LocalEvidenceReranker(EvidenceReranker):
    """Deterministic CPU reranker; replaceable by a local cross-encoder later."""

    def rerank(self, query: str, candidates: list[HybridSearchResult], top_k: int = 5) -> list[HybridSearchResult]:
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")
        query_text = query.strip().lower()
        query_tokens = set(extract_tokens(query_text))
        scored: list[tuple[float, HybridSearchResult]] = []
        for candidate in candidates:
            chunk = candidate.chunk
            content = str(getattr(chunk, "content", "")).lower()
            document = getattr(chunk, "document", None)
            title = str(getattr(document, "title", "")).lower()
            content_tokens = set(extract_tokens(content))
            coverage = len(query_tokens & content_tokens) / max(len(query_tokens), 1)
            title_coverage = len(query_tokens & set(extract_tokens(title))) / max(len(query_tokens), 1)
            phrase = 1.0 if query_text and query_text in content else 0.0
            # Exact identifiers (ICD-10, J18.9, invoice-001, etc.) deserve a
            # modest boost without allowing generic words to dominate.
            identifiers = [token for token in query_tokens if any(char.isdigit() for char in token) or "." in token or "/" in token]
            identifier_match = sum(token in content for token in identifiers) / max(len(identifiers), 1) if identifiers else 0.0
            score = candidate.fusion_score + (0.35 * coverage) + (0.2 * title_coverage) + (0.3 * phrase) + (0.25 * identifier_match)
            scored.append((score, candidate))
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return [candidate for _, candidate in scored[:top_k]]
