"""Initialize and load synthetic fixtures into the evaluation database only."""
from pathlib import Path

from .config import ensure_evaluation_environment
from .db import get_evaluation_session_factory
from .fixtures import load_controlled_fixtures
from .init_db import initialize_evaluation_database


def main() -> None:
    ensure_evaluation_environment(require_isolated=True)
    initialize_evaluation_database()
    path = Path(__file__).resolve().parents[2] / "tests/evaluation/fixtures/knowledge_documents.json"
    session = get_evaluation_session_factory()()
    try:
        loaded = load_controlled_fixtures(session, path)
    finally:
        session.close()
    print(f"Evaluation database initialized; loaded {loaded} new document(s).")


if __name__ == "__main__":
    main()
