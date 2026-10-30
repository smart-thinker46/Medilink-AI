from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # The JSON-only development path does not require python-dotenv.
    load_dotenv = None

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def require_database_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured. Copy .env.example to .env and set it.")
    return DATABASE_URL
