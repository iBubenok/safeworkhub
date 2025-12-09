"""SQLAlchemy модели данных.

Все модели экспортируются из этого модуля для удобства импорта
и обеспечения корректной работы Alembic.
"""

from app.models.user import User
from app.models.organization import Organization, OrganizationUser
from app.models.subscription import Subscription, Tariff
from app.models.material import Material, Category, Document
from app.models.course import Course, Module, Test, TestAttempt

__all__ = [
    "User",
    "Organization",
    "OrganizationUser",
    "Subscription",
    "Tariff",
    "Material",
    "Category",
    "Document",
    "Course",
    "Module",
    "Test",
    "TestAttempt",
]
