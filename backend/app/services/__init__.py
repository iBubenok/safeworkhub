"""Сервисный слой с бизнес-логикой."""

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.material_service import MaterialService

__all__ = [
    "AuthService",
    "UserService",
    "MaterialService",
]
