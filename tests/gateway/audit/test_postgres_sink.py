from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from medilink_ai.gateway.audit.db_models import GatewayAuditEventRecord
from medilink_ai.gateway.audit.models import AuditEvent, AuditEventType, AuditOutcome
from medilink_ai.gateway.audit.postgres_sink import PostgresAuditSink


def test_audit_sink_persists_event_in_sqlite_mapping():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    GatewayAuditEventRecord.__table__.create(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    PostgresAuditSink(session_factory).append(AuditEvent(AuditEventType.REQUEST_COMPLETED, "request-001", AuditOutcome.SUCCESS))
    with session_factory() as session:
        assert session.scalar(select(GatewayAuditEventRecord).where(GatewayAuditEventRecord.request_id == "request-001")) is not None
