from .postgres_sink import PostgresAuditSink
from .service import AuditService


def create_audit_service(session_factory) -> AuditService:
    return AuditService(PostgresAuditSink(session_factory))
