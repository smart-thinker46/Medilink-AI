"""Database boundary for isolated evaluation runs."""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is listed in requirements
    load_dotenv = None

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def get_evaluation_database_url() -> str:
    url = os.getenv("EVALUATION_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "EVALUATION_DATABASE_URL is not configured. Set it in medilink_ai/.env "
            "or export it before running the isolated evaluation."
        )
    return url


def create_evaluation_engine():
    return create_engine(get_evaluation_database_url(), pool_pre_ping=True, future=True)


def get_evaluation_session_factory():
    return sessionmaker(bind=create_evaluation_engine(), autoflush=False, autocommit=False, expire_on_commit=False)
