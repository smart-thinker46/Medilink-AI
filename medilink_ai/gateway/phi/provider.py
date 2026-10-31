from __future__ import annotations

from typing import Any, Mapping, Protocol

from ..context.models import ValidatedRequestContext


class HMISPHIDataProvider(Protocol):
    async def fetch_patient_projection(self, *, context: ValidatedRequestContext, allowed_fields: frozenset[str]) -> Mapping[str, Any]: ...
    async def fetch_encounter_projection(self, *, context: ValidatedRequestContext, allowed_fields: frozenset[str]) -> Mapping[str, Any]: ...


class PHIQueryInspector(Protocol):
    async def inspect_query(self, *, query: str, capability: str, purpose: str) -> str: ...
