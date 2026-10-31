from medilink_ai.knowledge.access import KnowledgeAccessContext
from medilink_ai.knowledge.database_filters import build_authorized_knowledge_statement


def test_authorized_query_is_tenant_and_facility_scoped():
    context = KnowledgeAccessContext(
        user_id="evaluation-user",
        organization_id="org-001",
        facility_id="facility-001",
        department_id="administration",
        roles=frozenset({"ADMIN_USER"}),
        classification_level="INTERNAL",
    )
    statement = build_authorized_knowledge_statement(context)
    compiled = str(statement.compile(compile_kwargs={"literal_binds": False}))
    assert "organization_id" in compiled
    assert "facility_id" in compiled
    assert "classification" in compiled


def test_authorized_query_does_not_use_a_client_supplied_facility_list():
    context = KnowledgeAccessContext(
        user_id="evaluation-user",
        organization_id="org-001",
        facility_id="facility-001",
        department_id=None,
        roles=frozenset({"ADMIN_USER"}),
        classification_level="INTERNAL",
    )
    statement = build_authorized_knowledge_statement(context)
    compiled = statement.compile().params
    assert compiled.get("facility_id_1") == "facility-001"
    assert "facility-002" not in str(compiled)
