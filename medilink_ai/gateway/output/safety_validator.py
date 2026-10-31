from __future__ import annotations

import re

from .models import OutputFailureType, OutputValidationFailure


FORBIDDEN_OUTPUT_PATTERNS = (
    (re.compile(r"\bapprove\b.*\bdischarge\b", re.I | re.S), "OUTPUT_ATTEMPTS_DISCHARGE_APPROVAL", OutputFailureType.FORBIDDEN_ACTION),
    (re.compile(r"\bauthori[sz]e\b.*\bmedication\b", re.I | re.S), "OUTPUT_ATTEMPTS_MEDICATION_AUTHORIZATION", OutputFailureType.FORBIDDEN_ACTION),
    (re.compile(r"\bapprove\b.*\bsurgery\b", re.I | re.S), "OUTPUT_ATTEMPTS_SURGERY_APPROVAL", OutputFailureType.FORBIDDEN_ACTION),
    (re.compile(r"\bexecute\b.*\brefund\b", re.I | re.S), "OUTPUT_ATTEMPTS_REFUND_EXECUTION", OutputFailureType.FORBIDDEN_ACTION),
    (re.compile(r"\b(?:change|modify|update)\b.*\b(?:billing|patient.{0,20}balance)\b", re.I | re.S), "OUTPUT_ATTEMPTS_BILLING_MODIFICATION", OutputFailureType.FORBIDDEN_ACTION),
    (re.compile(r"\b(?:authorize|approve)\b.*\b(?:transfusion|blood release)\b", re.I | re.S), "OUTPUT_ATTEMPTS_TRANSFUSION_AUTHORIZATION", OutputFailureType.FORBIDDEN_ACTION),
)


def validate_output_safety(text: str) -> tuple[OutputValidationFailure, ...]:
    return tuple(OutputValidationFailure(kind, reason) for pattern, reason, kind in FORBIDDEN_OUTPUT_PATTERNS if pattern.search(text))
