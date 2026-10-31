from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import GatewayExecutionContext


class AICapabilityHandler(ABC):
    capability: str

    @abstractmethod
    async def execute(self, *, context: GatewayExecutionContext, query: str) -> Any:
        raise NotImplementedError
