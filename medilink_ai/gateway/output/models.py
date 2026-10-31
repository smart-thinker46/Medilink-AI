from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class OutputValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


class OutputFailureType(str, Enum):
    SCHEMA_ERROR = "SCHEMA_ERROR"
    INVALID_CITATION = "INVALID_CITATION"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    SAFETY_VIOLATION = "SAFETY_VIOLATION"
    PHI_LEAKAGE = "PHI_LEAKAGE"
    FORBIDDEN_ACTION = "FORBIDDEN_ACTION"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    MALFORMED_OUTPUT = "MALFORMED_OUTPUT"


@dataclass(frozen=True)
class OutputValidationFailure:
    failure_type: OutputFailureType
    reason_code: str


@dataclass(frozen=True)
class OutputValidationResult:
    status: OutputValidationStatus
    response: Any | None
    failures: tuple[OutputValidationFailure, ...] = ()
