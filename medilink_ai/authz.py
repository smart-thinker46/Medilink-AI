"""Authorization adapter. In production, replace `Authorizer` with a call into Medilink's own
authorization layer. The AI never gets its own database account or its own permission model."""
from __future__ import annotations
from dataclasses import dataclass, field

ROLE_PERMISSIONS = {
    "doctor": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates"},
    "nurse": {"ai.summary", "ai.knowledge"},
    "registration": {"ai.knowledge", "ai.duplicates"},
    "billing": {"ai.knowledge", "ai.revenue"},
    "operations": {"ai.knowledge", "ai.queue", "ai.feedback"},
    # Canonical Medilink governance roles.  These are conservative capability
    # defaults until dedicated ai.* grants are configured in RBAC.
    "facility_admin": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates", "ai.queue", "ai.revenue", "ai.feedback"},
    "hospital_admin": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates", "ai.queue", "ai.revenue", "ai.feedback"},
    "super_admin": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates", "ai.queue", "ai.revenue", "ai.feedback"},
    "tenant_admin": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates", "ai.queue", "ai.revenue", "ai.feedback"},
    "medical_director": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates", "ai.queue", "ai.feedback"},
    "clinical_officer": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates"},
    "pharmacist": {"ai.summary", "ai.knowledge"},
    "lab_tech": {"ai.summary", "ai.knowledge"},
    # Roles already used by the Medilink backend, including the aliases that
    # can be created by a facility during user administration.
    "admin": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates", "ai.queue", "ai.revenue", "ai.feedback"},
    "administrator": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates", "ai.queue", "ai.revenue", "ai.feedback"},
    "facility_administrator": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates", "ai.queue", "ai.revenue", "ai.feedback"},
    "receptionist": {"ai.knowledge", "ai.duplicates"},
    "front_desk": {"ai.knowledge", "ai.duplicates"},
    "records_officer": {"ai.summary", "ai.knowledge", "ai.duplicates"},
    "specialist": {"ai.summary", "ai.note_draft", "ai.knowledge", "ai.duplicates"},
    "registered_nurse": {"ai.summary", "ai.knowledge"},
}


@dataclass
class User:
    id: str
    role: str
    assigned_patients: set = field(default_factory=set)  # care-team relationship
    permissions: set = field(default_factory=set)
    facility_id: str | None = None


class Authorizer:
    def can(self, user: User, permission: str, patient_id: str | None = None) -> bool:
        # In production, permissions originate from Medilink RBAC.  The small
        # role map remains solely as an explicit demo fallback.
        role = str(user.role or "").strip().lower().replace("-", "_").replace(" ", "_")
        granted = user.permissions or ROLE_PERMISSIONS.get(role, set())
        if permission not in granted:
            return False
        # A real backend-backed reader enforces patient visibility using the
        # caller's bearer token. Demo users retain the local care-team check.
        if patient_id is not None and user.assigned_patients and patient_id not in user.assigned_patients:
            return False  # no care-team relationship -> same denial the EMR would give
        return True
