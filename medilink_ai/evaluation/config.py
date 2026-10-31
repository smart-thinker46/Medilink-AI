from __future__ import annotations

import os


class EvaluationConfigurationError(RuntimeError):
    pass


def ensure_evaluation_environment(require_isolated: bool = False) -> None:
    environment = os.getenv("MEDILINK_ENVIRONMENT", os.getenv("MEDILINK_ENV", "development")).lower()
    if environment not in {"development", "test", "evaluation"}:
        raise EvaluationConfigurationError(
            f"Evaluation execution is blocked because MEDILINK_ENVIRONMENT={environment!r}."
        )
    if require_isolated and environment != "evaluation":
        raise EvaluationConfigurationError(
            "Loading synthetic fixtures requires MEDILINK_ENVIRONMENT=evaluation and a separate evaluation database."
        )
