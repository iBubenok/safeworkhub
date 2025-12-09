"""Главный модуль приложения FastAPI."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import close_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Управление жизненным циклом приложения.

    Выполняет инициализацию при старте и очистку при остановке.
    """
    # Startup
    yield
    # Shutdown
    await close_db()


def create_application() -> FastAPI:
    """Фабрика приложения FastAPI.

    Returns:
        Настроенный экземпляр FastAPI.
    """
    application = FastAPI(
        title=settings.app_name,
        description="Корпоративная SaaS-платформа по охране труда",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Обработчик ошибок приложения
    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Обработчик пользовательских исключений."""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    # Подключение роутеров
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    return application


app = create_application()


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Корневой эндпоинт."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": f"{settings.api_v1_prefix}/docs" if settings.is_development else "disabled",
    }
