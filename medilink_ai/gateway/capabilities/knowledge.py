from __future__ import annotations

from typing import Any

from .base import AICapabilityHandler
from ..models import GatewayExecutionContext


class KnowledgeAskCapability(AICapabilityHandler):
    capability = "knowledge.ask"

    def __init__(self, assistant):
        self.assistant = assistant

    async def execute(self, *, context: GatewayExecutionContext, query: str) -> Any:
        result = self.assistant.ask(query=query, context=context)
        if hasattr(result, "__await__"):
            return await result
        return result
