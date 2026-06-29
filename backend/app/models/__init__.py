"""SQLAlchemy модели данных.

Все модели экспортируются из этого модуля для удобства импорта
и обеспечения корректной работы Alembic.
"""

from app.models.attachment import MaterialAttachment
from app.models.audit_log import AuditLog
from app.models.checklist import (
    Checklist,
    ChecklistAnswerType,
    ChecklistItem,
    ChecklistItemReference,
    ChecklistNodeType,
    ChecklistStatus,
)
from app.models.course import AssignmentStatus, Course, CourseAssignment, CourseModule
from app.models.material import (
    Category,
    Material,
    MaterialContentFormat,
    MaterialStatus,
    MaterialType,
    MaterialVisibility,
    NpaActKind,
    NpaLevel,
    NpaStatus,
)
from app.models.material_version import MaterialVersion
from app.models.news import News
from app.models.notification import Notification, NotificationSettings
from app.models.npa import Npa
from app.models.organization import Organization, OrganizationUser, OrgRole
from app.models.refresh_session import RefreshSession
from app.models.subscription import Subscription, SubscriptionStatus, Tariff
from app.models.user import User

__all__ = [
    "AssignmentStatus",
    "AuditLog",
    "Category",
    "Checklist",
    "ChecklistAnswerType",
    "ChecklistItem",
    "ChecklistItemReference",
    "ChecklistNodeType",
    "ChecklistStatus",
    "Course",
    "CourseAssignment",
    "CourseModule",
    "Material",
    "MaterialAttachment",
    "MaterialContentFormat",
    "MaterialStatus",
    "MaterialType",
    "MaterialVersion",
    "MaterialVisibility",
    "News",
    "Notification",
    "NotificationSettings",
    "Npa",
    "NpaActKind",
    "NpaLevel",
    "NpaStatus",
    "OrgRole",
    "Organization",
    "OrganizationUser",
    "RefreshSession",
    "Subscription",
    "SubscriptionStatus",
    "Tariff",
    "User",
]
