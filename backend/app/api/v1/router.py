"""Главный роутер API v1."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, materials, health

api_router = APIRouter()

# Подключение эндпоинтов
api_router.include_router(health.router, tags=["Мониторинг"])
api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
api_router.include_router(materials.router, prefix="/materials", tags=["База знаний"])
