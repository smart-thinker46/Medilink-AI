from __future__ import annotations

from .base import AICapabilityHandler


class CapabilityRegistry:
    def __init__(self, handlers: list[AICapabilityHandler] | None = None):
        self._handlers: dict[str, AICapabilityHandler] = {}
        for handler in handlers or []:
            self.register(handler)

    def register(self, handler: AICapabilityHandler) -> None:
        capability = handler.capability.strip()
        if not capability:
            raise ValueError("Capability name cannot be empty.")
        if capability in self._handlers:
            raise ValueError(f"Capability already registered: {capability}")
        self._handlers[capability] = handler

    def get(self, capability: str) -> AICapabilityHandler:
        try:
            return self._handlers[capability]
        except KeyError as exc:
            raise KeyError(f"No AI capability handler registered: {capability}") from exc
