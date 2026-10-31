from .models import AuditEvent


class InMemoryAuditSink:
    def __init__(self):
        self.events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)
