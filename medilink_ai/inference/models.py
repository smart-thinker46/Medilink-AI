from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GenerationRequest:
    system_prompt: str
    user_prompt: str
    model: str
    temperature: float = 0.1
    max_tokens: int = 400
    response_format: str | None = "json"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResponse:
    content: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_duration_ns: int | None = None
    load_duration_ns: int | None = None
    prompt_duration_ns: int | None = None
    generation_duration_ns: int | None = None
