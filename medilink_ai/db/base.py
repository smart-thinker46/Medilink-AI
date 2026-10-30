try:
    from sqlalchemy.orm import DeclarativeBase
except ImportError:  # Keep JSON-only mode importable without SQLAlchemy installed.
    class DeclarativeBase:
        pass


class Base(DeclarativeBase):
    pass
