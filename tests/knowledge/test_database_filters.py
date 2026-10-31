from medilink_ai.knowledge.access import KnowledgeAccessContext
from medilink_ai.knowledge.database_filters import build_authorized_knowledge_statement


def test_authorized_statement_contains_tenant_and_access_conditions():
    context = KnowledgeAccessContext("user-1", "org-a", "facility-a", "pharmacy", frozenset({"PHARMACY_ADMIN"}), "INTERNAL")
    statement = build_authorized_knowledge_statement(context)
    compiled = str(statement.compile(compile_kwargs={"literal_binds": False}))
    assert "organization_id" in compiled
    assert "facility_id" in compiled
    assert "classification" in compiled
