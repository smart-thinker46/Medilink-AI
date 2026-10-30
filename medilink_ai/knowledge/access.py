from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeAccessContext:
    user_id: str
    organization_id: str
    facility_id: str
    department_id: str | None
    roles: frozenset[str]
    classification_level: str = "INTERNAL"
