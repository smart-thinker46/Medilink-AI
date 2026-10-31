from __future__ import annotations

from abc import ABC, abstractmethod

from .models import GenerationRequest, GenerationResponse


class InferenceProvider(ABC):
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
