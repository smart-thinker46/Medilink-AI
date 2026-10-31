from __future__ import annotations

from typing import Protocol


class GatewayMetrics(Protocol):
    def increment(self, name: str, *, labels: dict[str, str] | None = None) -> None: ...
    def observe(self, name: str, value: float, *, labels: dict[str, str] | None = None) -> None: ...


class InMemoryGatewayMetrics:
    def __init__(self):
        self.counters: dict[tuple, int] = {}
        self.observations: dict[tuple, list[float]] = {}

    @staticmethod
    def _key(name: str, labels: dict[str, str] | None):
        return name, tuple(sorted((labels or {}).items()))

    def increment(self, name: str, *, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + 1

    def observe(self, name: str, value: float, *, labels: dict[str, str] | None = None) -> None:
        self.observations.setdefault(self._key(name, labels), []).append(float(value))
