"""Read-only bridge to the Medilink backend.

This adapter deliberately forwards the signed-in user's bearer token.  It never
uses a database connection, service super-user, or an AI-specific credential,
so Medilink remains the authority for tenant, role and patient visibility.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from .authz import User
from .llm import assert_local_endpoint


class BackendAccessError(Exception):
    """The backend rejected, timed out, or could not safely serve a read."""


def _value(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


AI_ANALYTICS_MODULE_ID = "23"


def _ai_permissions_from_access(access: dict[str, Any], role: str) -> set[str]:
    """Map existing Medilink RBAC facts to AI capabilities.

    Medilink's `/security/access/me` emits its normal `permissions` collection,
    not a separate `aiPermissions` collection.  The AI gateway must therefore
    honour explicit `ai.*` grants and the AI Analytics module (module 23), while
    retaining role defaults only for established Medilink roles.
    """
    from .authz import ROLE_PERMISSIONS

    raw_permissions = access.get("permissions") or []
    tokens = {
        str(value).strip().lower()
        for value in raw_permissions
        if isinstance(value, str) and str(value).strip()
    }
    explicit_ai = {token for token in tokens if token.startswith("ai.")}
    if explicit_ai:
        return explicit_ai

    module_actions = {
        parts[2]
        for token in tokens
        for parts in [token.upper().split(":")]
        if len(parts) >= 3 and parts[0] == "MODULE" and parts[1] == AI_ANALYTICS_MODULE_ID
    }
    grants: set[str] = set()
    if "VIEW" in module_actions:
        grants.update({"ai.summary", "ai.knowledge"})
    if "CREATE" in module_actions:
        grants.update({"ai.summary", "ai.note_draft", "ai.knowledge"})
    if "APPROVE" in module_actions:
        grants.update({"ai.duplicates", "ai.queue", "ai.revenue", "ai.feedback"})
    if grants:
        return grants

    normalized_role = role.lower().replace("-", "_").replace(" ", "_")
    return set(ROLE_PERMISSIONS.get(normalized_role, set()))


class MedilinkBackend:
    def __init__(self, base_url: str, allowed_hosts: tuple[str, ...] = (), timeout_s: float = 10.0):
        assert_local_endpoint(base_url, allowed_hosts)
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _get(self, path: str, token: str) -> Any:
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=self.timeout_s,
            )
        except httpx.HTTPError as exc:
            raise BackendAccessError("Medilink backend is unavailable.") from exc
        if response.status_code in {401, 403}:
            raise BackendAccessError("Medilink denied this request.")
        if response.status_code == 404:
            raise BackendAccessError("The requested Medilink record was not found.")
        try:
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise BackendAccessError("Medilink returned an invalid response.") from exc

    def resolve_user(self, token: str) -> User:
        access = self._get("/security/access/me", token)
        # The access endpoint intentionally returns authorization facts only;
        # the stable subject is supplied by the profile endpoint.  Keep both
        # calls delegated to the user's existing Medilink bearer token.
        profile = self._get("/security/me", token)
        role = _value(access, "roleName", "roleLabel", "role") or _value(profile, "role", "roleLabel") or "user"
        permissions = _ai_permissions_from_access(access, role)
        return User(
            id=_value(profile, "sub", "id", "userId") or _value(access, "userId", "id", "sub"),
            role=role.lower().replace("-", "_").replace(" ", "_"),
            permissions=permissions,
            facility_id=_value(profile, "tenantId", "facilityId") or _value(access, "facilityId", "tenantId") or None,
        )

    def patient_record(self, patient_id: str, token: str) -> dict[str, Any]:
        row = self._get(f"/patients/{patient_id}", token)
        # Only map clinically relevant, already-authorised fields. Names, phone,
        # national ID, address and insurance identifiers are not copied.
        prescriptions = row.get("prescriptions") or []
        allergies = row.get("allergies") or row.get("allergyHistory") or []
        results = row.get("results") or row.get("laboratoryResults") or []
        encounters = row.get("encounters") or row.get("visits") or []
        conditions = row.get("conditions") or row.get("diagnoses") or []
        def items(values: Any, ref_prefix: str, text_keys: tuple[str, ...]) -> list[dict[str, str]]:
            answer = []
            for index, item in enumerate(values if isinstance(values, list) else []):
                data = item if isinstance(item, dict) else {"text": item}
                text = _value(data, *text_keys)
                if text:
                    answer.append({"text": text, "ref": _value(data, "id", "recordId") or f"{ref_prefix}-{index + 1}", "date": _value(data, "date", "createdAt", "resultDate")})
            return answer
        return {
            "conditions": items(conditions, "condition", ("name", "diagnosis", "text", "description")),
            "allergies": items(allergies, "allergy", ("allergen", "name", "text", "description")),
            "medications": items(prescriptions, "medication", ("medicationName", "drugName", "name", "text")),
            "results": items(results, "result", ("summary", "result", "value", "text", "description")),
            "encounters": items(encounters, "encounter", ("summary", "chiefComplaint", "reason", "text", "description")),
        }

    def search_patients(self, query: str, token: str) -> list[dict[str, str]]:
        """Return a minimal, authorised picker list; no clinical detail leaks here."""
        value = query.strip()
        if len(value) < 2:
            return []
        data = self._get(f"/patients/search/universal?q={quote(value)}", token)
        rows = data if isinstance(data, list) else data.get("data") or data.get("items") or []
        matches = []
        for row in rows if isinstance(rows, list) else []:
            patient = row.get("patient") if isinstance(row, dict) else None
            patient = patient if isinstance(patient, dict) else row if isinstance(row, dict) else {}
            patient_id = _value(patient, "id", "patientId")
            if not patient_id:
                continue
            name = " ".join(filter(None, [_value(patient, "firstName", "givenName"), _value(patient, "middleName"), _value(patient, "lastName", "familyName")])) or _value(patient, "name", "fullName") or "Patient"
            matches.append({"id": patient_id, "name": name, "mrn": _value(patient, "mrn", "patientCode", "patientId")})
        return matches[:25]


class BackendHMISReader:
    """Per-request reader: the token is never retained beyond the request."""
    def __init__(self, backend: MedilinkBackend, token: str):
        self.backend, self.token = backend, token

    def get_patient_record(self, patient_id: str) -> dict[str, Any]:
        return self.backend.patient_record(patient_id, self.token)
