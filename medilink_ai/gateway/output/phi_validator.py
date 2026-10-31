from __future__ import annotations

import re

from .models import OutputFailureType, OutputValidationFailure


PHI_PATTERNS = (
    (re.compile(r"\b\d{10}\b"), "POTENTIAL_IDENTIFIER"),
    (re.compile(r"\b[A-Z]{2}\d{6,10}\b"), "POTENTIAL_MEDICAL_IDENTIFIER"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "POTENTIAL_EMAIL"),
    (re.compile(r"\b(?:\+254|0)7\d{8}\b"), "POTENTIAL_KENYAN_PHONE"),
)


def validate_output_phi(text: str) -> tuple[OutputValidationFailure, ...]:
    return tuple(OutputValidationFailure(OutputFailureType.PHI_LEAKAGE, reason) for pattern, reason in PHI_PATTERNS if pattern.search(text))
