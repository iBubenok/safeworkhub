"""Репозитории для работы с данными."""

from app.db.repositories.base import BaseRepository
from app.db.repositories.category_repository import CategoryRepository
from app.db.repositories.course_repository import CourseAssignmentRepository, CourseRepository
from app.db.repositories.material_repository import MaterialRepository
from app.db.repositories.organization_repository import OrganizationRepository
from app.db.repositories.refresh_session_repository import RefreshSessionRepository
from app.db.repositories.subscription_repository import SubscriptionRepository, TariffRepository
from app.db.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "CategoryRepository",
    "CourseAssignmentRepository",
    "CourseRepository",
    "MaterialRepository",
    "OrganizationRepository",
    "RefreshSessionRepository",
    "SubscriptionRepository",
    "TariffRepository",
    "UserRepository",
]
