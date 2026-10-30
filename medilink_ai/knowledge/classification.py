CLASSIFICATION_LEVELS = {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "RESTRICTED": 3}


def normalize_classification(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if normalized not in CLASSIFICATION_LEVELS:
        raise ValueError(f"Unknown classification: {value}")
    return normalized


def can_access_classification(user_level: str, document_level: str) -> bool:
    return CLASSIFICATION_LEVELS[normalize_classification(user_level)] >= CLASSIFICATION_LEVELS[normalize_classification(document_level)]
