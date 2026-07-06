"""Главный модуль приложения FastAPI."""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import close_db
from app.tasks.deadline_reminders import deadline_reminder_loop

logger = structlog.get_logger(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Количество HTTP-запросов",
    ["method", "path", "status"],
    namespace=settings.metrics_namespace,
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "Латентность HTTP-запросов",
    ["method", "path"],
    namespace=settings.metrics_namespace,
)


def problem_response(request: Request, exc: AppError) -> JSONResponse:
    """Формирование ответа в формате Problem Details."""
    request_id = getattr(request.state, "request_id", None)
    payload = exc.to_dict()
    if request_id:
        payload["error"]["request_id"] = request_id
    return JSONResponse(status_code=exc.status_code, content=payload)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Управление жизненным циклом приложения."""
    reminder_task: asyncio.Task[None] | None = None
    if not settings.is_testing:
        reminder_task = asyncio.create_task(deadline_reminder_loop())
    try:
        yield
    finally:
        if reminder_task is not None:
            reminder_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await reminder_task
        await close_db()


def create_application() -> FastAPI:
    """Фабрика приложения FastAPI."""
    application = FastAPI(
        title=settings.app_name,
        description="Корпоративная SaaS-платформа по охране труда",
        version="0.2.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def request_context_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(settings.request_id_header) or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except AppError as exc:
            return problem_response(request, exc)
        except Exception:
            logger.exception("Unhandled server error", request_id=request_id)
            if settings.debug:
                raise
            payload = {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Внутренняя ошибка сервера",
                    "details": {},
                    "request_id": request_id,
                }
            }
            return JSONResponse(status_code=500, content=payload)

        duration = time.perf_counter() - start
        REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
        response.headers[settings.request_id_header] = request_id
        return response

    # CORS добавляем последним, чтобы он был самым внешним слоем и проставлял заголовки
    # даже на ответы-ошибки, которые формирует request_context_middleware (иначе браузер
    # блокирует тело 4xx/5xx кросс-доменного ответа и клиент видит «Произошла ошибка»).
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.api_v1_prefix)

    if settings.prometheus_enabled:

        @application.get("/metrics", include_in_schema=False)
        async def metrics() -> Response:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @application.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": "0.2.0",
            "docs": f"{settings.api_v1_prefix}/docs" if settings.is_development else "disabled",
        }

    return application


app = create_application()
