from __future__ import annotations

from typing import Protocol

from .models import AuditEvent


class AuditSink(Protocol):
    def append(self, event: AuditEvent) -> None:
        ...
