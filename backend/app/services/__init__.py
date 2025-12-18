"""Сервисный слой с бизнес-логикой."""

from app.services.auth_service import AuthService
from app.services.course_service import CourseService
from app.services.material_service import MaterialService
from app.services.user_service import UserService

__all__ = [
    "AuthService",
    "CourseService",
    "MaterialService",
    "UserService",
]
