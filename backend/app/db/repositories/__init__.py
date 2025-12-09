"""Репозитории для работы с данными."""

from app.db.repositories.base import BaseRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.organization_repository import OrganizationRepository
from app.db.repositories.material_repository import MaterialRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "OrganizationRepository",
    "MaterialRepository",
]
