from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from .citation_validator import validate_citations
from .models import OutputFailureType, OutputValidationFailure, OutputValidationResult, OutputValidationStatus
from .phi_validator import validate_output_phi
from .safety_validator import validate_output_safety
from .schemas import GatewayAIResponse


class AIOutputValidationService:
    """Treats every model response as untrusted until deterministic checks pass."""

    def validate(self, *, raw_output: Any, allowed_source_ids: set[str], human_review_required: bool = False) -> OutputValidationResult:
        try:
            response = raw_output if isinstance(raw_output, GatewayAIResponse) else GatewayAIResponse.model_validate(raw_output)
        except (ValidationError, TypeError, ValueError):
            return OutputValidationResult(
                OutputValidationStatus.INVALID, None,
                (OutputValidationFailure(OutputFailureType.SCHEMA_ERROR, "OUTPUT_SCHEMA_INVALID"),),
            )

        citation_failures = validate_citations(response.citations, allowed_source_ids)
        if citation_failures:
            return OutputValidationResult(OutputValidationStatus.INVALID, None, citation_failures)
        safety_failures = validate_output_safety(response.answer)
        phi_failures = validate_output_phi(response.answer)
        if safety_failures or phi_failures:
            return OutputValidationResult(OutputValidationStatus.BLOCKED, None, safety_failures + phi_failures)

        if human_review_required:
            if not response.human_review_required:
                failure = OutputValidationFailure(OutputFailureType.HUMAN_REVIEW_REQUIRED, "HUMAN_REVIEW_REQUIRED")
                # Preserve the response but force the authoritative gateway flag.
                response = response.model_copy(update={"human_review_required": True})
                return OutputValidationResult(OutputValidationStatus.REVIEW_REQUIRED, response, (failure,))
            return OutputValidationResult(OutputValidationStatus.REVIEW_REQUIRED, response)
        return OutputValidationResult(OutputValidationStatus.VALID, response)
