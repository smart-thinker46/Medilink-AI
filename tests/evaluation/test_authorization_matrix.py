from datetime import date, timedelta

from medilink_ai.knowledge.access import KnowledgeAccessContext
from medilink_ai.knowledge.authorization import is_chunk_authorized
from medilink_ai.knowledge.models import DocumentMetadata, KnowledgeChunk


def make_chunk(**changes):
    values = {
        "document_id": "doc-1", "organization_id": "org-001", "facility_id": "facility-001",
        "department_id": "pharmacy", "title": "Policy", "document_type": "SOP",
        "classification": "INTERNAL", "version": "1.0", "allowed_roles": ["PHARMACY_ADMIN"],
        "allowed_users": [], "effective_from": None, "effective_until": None,
    }
    values.update(changes)
    metadata = DocumentMetadata(**values)
    return KnowledgeChunk("chunk-1", "doc-1", 0, "content", metadata)


def context(**changes):
    values = dict(user_id="user-001", organization_id="org-001", facility_id="facility-001",
                  department_id="pharmacy", roles=frozenset({"PHARMACY_ADMIN"}), classification_level="INTERNAL")
    values.update(changes)
    return KnowledgeAccessContext(**values)


def test_authorized_role_is_allowed():
    assert is_chunk_authorized(make_chunk(), context())


def test_wrong_organization_and_facility_are_denied_even_for_role():
    assert not is_chunk_authorized(make_chunk(organization_id="org-002"), context())
    assert not is_chunk_authorized(make_chunk(facility_id="facility-002"), context())


def test_classification_and_dates_are_enforced():
    assert not is_chunk_authorized(make_chunk(classification="RESTRICTED"), context())
    assert not is_chunk_authorized(make_chunk(effective_until=date.today() - timedelta(days=1)), context())
    assert not is_chunk_authorized(make_chunk(effective_from=date.today() + timedelta(days=1)), context())


def test_explicit_user_permission_does_not_bypass_tenant_boundary():
    assert is_chunk_authorized(make_chunk(allowed_roles=[], allowed_users=["user-001"]), context())
    assert not is_chunk_authorized(make_chunk(facility_id="facility-002", allowed_roles=[], allowed_users=["user-001"]), context())
