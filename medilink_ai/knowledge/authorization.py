from datetime import date
from .access import KnowledgeAccessContext
from .classification import can_access_classification
from .models import KnowledgeChunk


def is_effective_today(chunk: KnowledgeChunk, today: date | None = None) -> bool:
    today = today or date.today()
    metadata = chunk.metadata
    return not ((metadata.effective_from and today < metadata.effective_from) or (metadata.effective_until and today > metadata.effective_until))


def is_chunk_authorized(chunk: KnowledgeChunk, context: KnowledgeAccessContext, today: date | None = None) -> bool:
    metadata = chunk.metadata
    if metadata.organization_id != context.organization_id or metadata.facility_id != context.facility_id:
        return False
    if metadata.department_id and metadata.department_id != context.department_id:
        return False
    if not can_access_classification(context.classification_level, metadata.classification):
        return False
    roles = {str(role).strip().lower() for role in context.roles}
    allowed_roles = {str(role).strip().lower() for role in metadata.allowed_roles if str(role).strip()}
    allowed_users = {str(user).strip() for user in metadata.allowed_users if str(user).strip()}
    role_allowed = (not allowed_users and not allowed_roles) or "*" in allowed_roles or bool(roles.intersection(allowed_roles))
    user_allowed = not allowed_users or context.user_id in allowed_users
    if not (role_allowed or user_allowed):
        return False
    return is_effective_today(chunk, today)
