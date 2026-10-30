from __future__ import annotations

from collections.abc import Generator

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
except ImportError as exc:  # pragma: no cover - exercised only in uninstalled environments
    create_engine = None
    Session = object
    sessionmaker = None
    _SQLALCHEMY_ERROR = exc

from .config import require_database_url

_engine = None
_session_factory = None


def get_engine():
    """Create the engine only when the persistent store is explicitly used."""
    global _engine
    if _engine is None:
        if create_engine is None:
            raise RuntimeError("Install the database dependencies from requirements.txt.") from _SQLALCHEMY_ERROR
        _engine = create_engine(require_database_url(), pool_pre_ping=True)
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        if sessionmaker is None:
            raise RuntimeError("Install the database dependencies from requirements.txt.") from _SQLALCHEMY_ERROR
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
