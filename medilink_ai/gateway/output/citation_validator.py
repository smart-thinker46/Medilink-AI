from __future__ import annotations

from collections.abc import Iterable

from .models import OutputFailureType, OutputValidationFailure


def validate_citations(citations: Iterable, allowed_source_ids: set[str]) -> tuple[OutputValidationFailure, ...]:
    failures: list[OutputValidationFailure] = []
    for citation in citations:
        source_id = getattr(citation, "source_id", None)
        if not source_id:
            failures.append(OutputValidationFailure(OutputFailureType.INVALID_CITATION, "CITATION_SOURCE_ID_MISSING"))
        elif source_id not in allowed_source_ids:
            failures.append(OutputValidationFailure(OutputFailureType.INVALID_CITATION, "CITATION_SOURCE_NOT_IN_EVIDENCE"))
    return tuple(failures)
