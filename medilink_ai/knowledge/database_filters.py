"""SQL authorization predicates for knowledge retrieval."""
from __future__ import annotations

from datetime import date

from sqlalchemy import and_, or_, select

from .access import KnowledgeAccessContext
from .classification import CLASSIFICATION_LEVELS, normalize_classification
from .db_models import KnowledgeChunk, KnowledgeDocument


def build_authorized_knowledge_statement(
    context: KnowledgeAccessContext,
    today: date | None = None,
):
    """Build a statement that only returns authorized chunks and documents.

    ``allowed_roles`` and ``allowed_users`` are JSONB columns in the current
    schema, so JSON containment is used instead of trusting application-side
    filtering after retrieval.
    """
    current_day = today or date.today()
    user_level = normalize_classification(context.classification_level)
    allowed_classifications = [
        name for name, level in CLASSIFICATION_LEVELS.items()
        if level <= CLASSIFICATION_LEVELS[user_level]
    ]
    roles = {str(role).strip().lower() for role in context.roles if str(role).strip()}
    role_conditions = [KnowledgeDocument.allowed_roles == []]
    role_conditions.append(KnowledgeDocument.allowed_roles.contains(["*"]))
    role_conditions.extend(KnowledgeDocument.allowed_roles.contains([role]) for role in roles)
    user_conditions = [KnowledgeDocument.allowed_users == []]
    user_conditions.append(KnowledgeDocument.allowed_users.contains([context.user_id]))

    statement = (
        select(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .where(
            KnowledgeDocument.organization_id == context.organization_id,
            KnowledgeDocument.facility_id == context.facility_id,
            KnowledgeDocument.classification.in_(allowed_classifications),
            or_(KnowledgeDocument.department_id.is_(None), KnowledgeDocument.department_id == context.department_id),
            or_(KnowledgeDocument.effective_from.is_(None), KnowledgeDocument.effective_from <= current_day),
            or_(KnowledgeDocument.effective_until.is_(None), KnowledgeDocument.effective_until >= current_day),
            or_(and_(or_(*role_conditions), or_(*user_conditions)), KnowledgeDocument.allowed_users.contains([context.user_id])),
        )
    )
    return statement
