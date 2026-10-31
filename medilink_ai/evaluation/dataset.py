from __future__ import annotations

import json
from pathlib import Path

from .models import EvaluationCase


def load_evaluation_dataset(path: str | Path) -> list[EvaluationCase]:
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {dataset_path}")
    raw_cases = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(raw_cases, list):
        raise ValueError("Evaluation dataset must contain a JSON array.")
    cases: list[EvaluationCase] = []
    seen: set[str] = set()
    required = {"case_id", "category", "question", "organization_id", "facility_id", "roles", "classification_level", "expected_behavior"}
    for raw in raw_cases:
        if not isinstance(raw, dict) or not required.issubset(raw):
            raise ValueError("Each evaluation case must contain the required fields.")
        case_id = str(raw["case_id"]).strip()
        if not case_id or case_id in seen:
            raise ValueError(f"Duplicate or empty evaluation case id: {case_id!r}")
        if not str(raw["question"]).strip():
            raise ValueError(f"Evaluation case {case_id} has an empty question.")
        roles = raw["roles"]
        if not isinstance(roles, list) or not all(str(role).strip() for role in roles):
            raise ValueError(f"Evaluation case {case_id} roles must be a non-empty list.")
        seen.add(case_id)
        cases.append(EvaluationCase(
            case_id=case_id,
            category=raw["category"],
            question=str(raw["question"]),
            organization_id=str(raw["organization_id"]),
            facility_id=str(raw["facility_id"]),
            department_id=str(raw["department_id"]) if raw.get("department_id") is not None else None,
            roles=tuple(str(role) for role in roles),
            classification_level=str(raw["classification_level"]),
            expected_behavior=raw["expected_behavior"],
            expected_source_ids=tuple(str(value) for value in raw.get("expected_source_ids", [])),
            expected_document_ids=tuple(str(value) for value in raw.get("expected_document_ids", [])),
            expected_keywords=tuple(str(value) for value in raw.get("expected_keywords", [])),
            forbidden_keywords=tuple(str(value) for value in raw.get("forbidden_keywords", [])),
            notes=str(raw.get("notes", "")),
            severity=raw.get("severity", "MEDIUM"),
        ))
    return cases
