"""Главный роутер API v1."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, courses, health, materials, users, notifications, notifications_sse

api_router = APIRouter()

# Подключение эндпоинтов
api_router.include_router(health.router, tags=["Мониторинг"])
api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
api_router.include_router(materials.router, prefix="/materials", tags=["База знаний"])
api_router.include_router(courses.router, prefix="/courses", tags=["Курсы"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Уведомления"])
api_router.include_router(notifications_sse.router, prefix="/notifications", tags=["Уведомления"])
