from __future__ import annotations

import re

from .models import AIActionType


class SafetyActionClassifier:
    """Deterministic, conservative intent classifier; it never calls an LLM."""

    _PATTERNS: tuple[tuple[AIActionType, tuple[str, ...]], ...] = (
        (AIActionType.AUTHORIZE, (r"\bauthori[sz]e\b", r"\bgrant approval\b", r"\bpermit\b")),
        (AIActionType.APPROVE, (r"\bapprove\b", r"\bapproval\b", r"\bsign[ -]?off\b")),
        (AIActionType.MODIFY, (r"\bchange\b", r"\bmodify\b", r"\bupdate\b", r"\bdelete\b", r"\boverwrite\b", r"\balter\b")),
        (AIActionType.EXECUTE, (r"\bexecute\b", r"\bcarry out\b", r"\bcomplete the (?:discharge|refund|transfer)\b", r"\b(?:discharge|refund|transfer)\b.*\bautomatically\b")),
        (AIActionType.RECOMMEND, (r"\brecommend\b", r"\bsuggest\b", r"\bwhat should we do\b")),
        (AIActionType.DRAFT, (r"\bdraft\b", r"\bprepare a (?:note|report|letter)\b")),
        (AIActionType.SUMMARIZE, (r"\bsummar(?:y|ize|ise)\b", r"\bbrief(?:ly)?\b")),
        (AIActionType.EXPLAIN, (r"\bexplain\b", r"\bhow does\b", r"\bwhat is\b", r"\bprocedure\b")),
        (AIActionType.RETRIEVE, (r"\bfind\b", r"\blook up\b", r"\bretrieve\b", r"\bsearch\b")),
        (AIActionType.CLASSIFY, (r"\bclassif(?:y|ication)\b", r"\bcategor(?:y|ize|ise)\b")),
        (AIActionType.ANALYZE, (r"\banaly[sz]e\b", r"\bidentify (?:gaps|anomalies|issues)\b")),
    )

    def classify(self, query: str) -> AIActionType:
        if not isinstance(query, str) or not query.strip():
            return AIActionType.ANALYZE
        lowered = query.lower()
        for action, patterns in self._PATTERNS:
            if any(re.search(pattern, lowered) for pattern in patterns):
                return action
        return AIActionType.ANALYZE
