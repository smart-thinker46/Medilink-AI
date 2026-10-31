from __future__ import annotations

from collections.abc import Sequence


def precision_at_k(retrieved: Sequence[str], expected: set[str], k: int | None = None) -> float:
    if k is not None and k <= 0:
        raise ValueError("k must be greater than zero")
    values = retrieved[:k] if k is not None else retrieved
    if not values and k is None:
        return 0.0
    denominator = k if k is not None else len(values)
    return sum(item in expected for item in values) / denominator


def recall_at_k(retrieved: Sequence[str], expected: set[str], k: int | None = None) -> float:
    if not expected:
        return 1.0
    values = retrieved[:k] if k is not None else retrieved
    return len(set(values) & expected) / len(expected)


def reciprocal_rank(retrieved: Sequence[str], expected: set[str], k: int | None = None) -> float:
    values = retrieved[:k] if k is not None else retrieved
    for index, item in enumerate(values, start=1):
        if item in expected:
            return 1.0 / index
    return 0.0
