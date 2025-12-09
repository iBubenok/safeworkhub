# Руководство разработчика SafeWorkHub

## Структура проекта

```
repository/
├── backend/                     # Backend-приложение (Python/FastAPI)
│   ├── app/                     # Исходный код приложения
│   │   ├── api/                 # API-слой
│   │   │   └── v1/              # Версия API v1
│   │   │       ├── endpoints/   # Эндпоинты по модулям
│   │   │       └── router.py    # Главный роутер v1
│   │   ├── core/                # Ядро приложения
│   │   │   ├── config.py        # Конфигурация
│   │   │   ├── security.py      # Безопасность, JWT
│   │   │   ├── exceptions.py    # Базовые исключения
│   │   │   └── dependencies.py  # Общие зависимости FastAPI
│   │   ├── db/                  # Слой данных
│   │   │   ├── migrations/      # Alembic миграции
│   │   │   ├── repositories/    # Репозитории
│   │   │   ├── base.py          # Базовые классы SQLAlchemy
│   │   │   └── session.py       # Управление сессиями
│   │   ├── models/              # SQLAlchemy модели
│   │   ├── schemas/             # Pydantic схемы
│   │   ├── services/            # Бизнес-логика
│   │   ├── tasks/               # Celery задачи
│   │   └── utils/               # Утилиты
│   ├── tests/                   # Тесты
│   │   ├── unit/                # Модульные тесты
│   │   ├── integration/         # Интеграционные тесты
│   │   └── e2e/                 # End-to-end тесты
│   ├── pyproject.toml           # Конфигурация проекта Python
│   └── alembic.ini              # Конфигурация Alembic
│
├── frontend/                    # Frontend-приложение (React/TypeScript)
│   ├── src/
│   │   ├── api/                 # API-клиент
│   │   ├── components/          # React-компоненты
│   │   │   ├── common/          # Переиспользуемые компоненты
│   │   │   ├── features/        # Компоненты по функциям
│   │   │   └── layouts/         # Layout-компоненты
│   │   ├── hooks/               # Кастомные хуки
│   │   ├── pages/               # Страницы (роуты)
│   │   ├── store/               # Глобальное состояние
│   │   ├── styles/              # Глобальные стили
│   │   ├── types/               # TypeScript типы
│   │   └── utils/               # Утилиты
│   ├── public/                  # Статические файлы
│   ├── tests/                   # Тесты frontend
│   ├── package.json             # Зависимости npm
│   └── vite.config.ts           # Конфигурация Vite
│
├── infra/                       # Инфраструктура
│   ├── docker/                  # Docker-конфигурации
│   ├── ci/                      # CI/CD пайплайны
│   └── monitoring/              # Конфигурации мониторинга
│
├── docs/                        # Дополнительная документация
├── docker-compose.yml           # Локальная оркестрация
├── .env.example                 # Шаблон переменных окружения
└── .gitignore                   # Исключения Git
```

## Настройка окружения разработки

### Предварительные требования

- **Docker** 24+ и **Docker Compose** 2.20+
- **Python** 3.12+ (для локальной разработки backend)
- **Node.js** 20+ (для локальной разработки frontend)
- **Git** 2.40+

### Способ 1: Docker Compose (рекомендуется)

Самый простой способ запустить всё окружение:

```bash
# Клонирование репозитория
git clone https://github.com/iBubenok/safeworkhub.git
cd safeworkhub

# Копирование конфигурации
cp .env.example .env

# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f backend
```

После запуска доступны:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Способ 2: Локальная разработка

#### Backend

```bash
cd backend

# Создание виртуального окружения
python -m venv .venv

# Активация (Linux/macOS)
source .venv/bin/activate

# Активация (Windows)
.venv\Scripts\activate

# Установка зависимостей
pip install -e ".[dev]"

# Запуск PostgreSQL и Redis через Docker
docker compose up -d postgres redis

# Применение миграций
alembic upgrade head

# Запуск сервера разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev-сервера
npm run dev

# Сборка production
npm run build

# Проверка типов
npm run typecheck

# Линтинг
npm run lint
```

## Конфигурация

### Переменные окружения

Приложение конфигурируется через переменные окружения. Основные параметры:

```bash
# Общие
APP_ENV=development                    # development | staging | production
DEBUG=true                             # Режим отладки
SECRET_KEY=your-secret-key-here        # Секретный ключ для JWT

# База данных
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/safeworkhub
DATABASE_POOL_SIZE=20                  # Размер пула соединений
DATABASE_POOL_OVERFLOW=10              # Дополнительные соединения

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user
SMTP_PASSWORD=password
EMAIL_FROM=noreply@safeworkhub.ru

# S3/MinIO (файловое хранилище)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=safeworkhub
```

### Иерархия конфигурации

Порядок приоритета (от низшего к высшему):
1. Значения по умолчанию в коде
2. Файл `.env`
3. Переменные окружения системы
4. Переменные окружения Docker/Kubernetes

## Работа с базой данных

### Создание миграции

```bash
cd backend

# Автогенерация миграции по изменениям в моделях
alembic revision --autogenerate -m "описание_изменений"

# Создание пустой миграции (для ручного SQL)
alembic revision -m "описание_изменений"
```

### Применение миграций

```bash
# Применить все миграции
alembic upgrade head

# Применить одну миграцию вперёд
alembic upgrade +1

# Откатить одну миграцию
alembic downgrade -1

# Откатить все миграции
alembic downgrade base

# Показать текущую ревизию
alembic current

# Показать историю миграций
alembic history
```

### Соглашения для миграций

1. Каждая миграция должна быть атомарной и обратимой
2. Не изменять уже применённые миграции
3. Имена миграций: `YYYYMMDD_HHMM_краткое_описание`
4. Для данных использовать отдельные миграции от структуры

## Добавление нового модуля

### Шаг 1: Создание структуры

```
app/
├── modules/
│   └── new_module/
│       ├── __init__.py
│       ├── router.py           # FastAPI роутер
│       ├── schemas.py          # Pydantic схемы
│       ├── models.py           # SQLAlchemy модели (или импорт)
│       ├── service.py          # Бизнес-логика
│       ├── repository.py       # Доступ к данным
│       ├── dependencies.py     # FastAPI зависимости
│       └── exceptions.py       # Исключения модуля
```

### Шаг 2: Определение модели (models.py)

```python
"""Модели данных модуля."""

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class NewEntity(Base, UUIDMixin, TimestampMixin):
    """Новая доменная сущность."""

    __tablename__ = "new_entities"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="new_entities")
```

### Шаг 3: Создание схем (schemas.py)

```python
"""Pydantic схемы для валидации и сериализации."""

from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class NewEntityBase(BaseModel):
    """Базовая схема."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class NewEntityCreate(NewEntityBase):
    """Схема создания."""

    pass


class NewEntityUpdate(BaseModel):
    """Схема обновления (partial update)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class NewEntityResponse(NewEntityBase):
    """Схема ответа."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: int
```

### Шаг 4: Реализация репозитория (repository.py)

```python
"""Репозиторий для работы с данными."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.modules.new_module.models import NewEntity


class NewEntityRepository(BaseRepository[NewEntity]):
    """Репозиторий для NewEntity."""

    def __init__(self, session: AsyncSession):
        super().__init__(NewEntity, session)

    async def get_by_organization(
        self,
        organization_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NewEntity]:
        """Получить сущности по организации."""
        query = (
            select(NewEntity)
            .where(NewEntity.organization_id == organization_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
```

### Шаг 5: Реализация сервиса (service.py)

```python
"""Бизнес-логика модуля."""

from uuid import UUID

from app.modules.new_module.repository import NewEntityRepository
from app.modules.new_module.schemas import (
    NewEntityCreate,
    NewEntityUpdate,
    NewEntityResponse,
)
from app.modules.new_module.exceptions import NewEntityNotFoundError


class NewEntityService:
    """Сервис для работы с NewEntity."""

    def __init__(self, repository: NewEntityRepository):
        self.repository = repository

    async def create(
        self,
        organization_id: int,
        data: NewEntityCreate,
    ) -> NewEntityResponse:
        """Создать новую сущность."""
        entity = await self.repository.create(
            organization_id=organization_id,
            **data.model_dump(),
        )
        return NewEntityResponse.model_validate(entity)

    async def get_by_id(self, entity_id: UUID) -> NewEntityResponse:
        """Получить сущность по ID."""
        entity = await self.repository.get_by_id(entity_id)
        if not entity:
            raise NewEntityNotFoundError(entity_id)
        return NewEntityResponse.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: NewEntityUpdate,
    ) -> NewEntityResponse:
        """Обновить сущность."""
        entity = await self.repository.update(
            entity_id,
            **data.model_dump(exclude_unset=True),
        )
        if not entity:
            raise NewEntityNotFoundError(entity_id)
        return NewEntityResponse.model_validate(entity)

    async def delete(self, entity_id: UUID) -> None:
        """Удалить сущность."""
        deleted = await self.repository.delete(entity_id)
        if not deleted:
            raise NewEntityNotFoundError(entity_id)
```

### Шаг 6: Создание роутера (router.py)

```python
"""API-эндпоинты модуля."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user, get_db
from app.modules.new_module.dependencies import get_new_entity_service
from app.modules.new_module.schemas import (
    NewEntityCreate,
    NewEntityUpdate,
    NewEntityResponse,
)
from app.modules.new_module.service import NewEntityService

router = APIRouter(prefix="/new-entities", tags=["New Entities"])


@router.post(
    "",
    response_model=NewEntityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_entity(
    data: NewEntityCreate,
    service: NewEntityService = Depends(get_new_entity_service),
    current_user = Depends(get_current_user),
):
    """Создать новую сущность."""
    return await service.create(
        organization_id=current_user.organization_id,
        data=data,
    )


@router.get("/{entity_id}", response_model=NewEntityResponse)
async def get_entity(
    entity_id: UUID,
    service: NewEntityService = Depends(get_new_entity_service),
    current_user = Depends(get_current_user),
):
    """Получить сущность по ID."""
    return await service.get_by_id(entity_id)


@router.patch("/{entity_id}", response_model=NewEntityResponse)
async def update_entity(
    entity_id: UUID,
    data: NewEntityUpdate,
    service: NewEntityService = Depends(get_new_entity_service),
    current_user = Depends(get_current_user),
):
    """Обновить сущность."""
    return await service.update(entity_id, data)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: UUID,
    service: NewEntityService = Depends(get_new_entity_service),
    current_user = Depends(get_current_user),
):
    """Удалить сущность."""
    await service.delete(entity_id)
```

### Шаг 7: Регистрация роутера

В `app/api/v1/router.py`:

```python
from app.modules.new_module.router import router as new_module_router

api_router.include_router(new_module_router)
```

## Обработка ошибок

### Иерархия исключений

```python
# app/core/exceptions.py

class AppError(Exception):
    """Базовое исключение приложения."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    """Ресурс не найден."""

    def __init__(self, resource: str, resource_id: str | int):
        super().__init__(
            message=f"{resource} с ID {resource_id} не найден",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "id": str(resource_id)},
        )


class ValidationError(AppError):
    """Ошибка валидации."""

    def __init__(self, message: str, errors: list[dict]):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": errors},
        )


class AuthenticationError(AppError):
    """Ошибка аутентификации."""

    def __init__(self, message: str = "Требуется аутентификация"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(AppError):
    """Ошибка авторизации."""

    def __init__(self, message: str = "Доступ запрещён"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
        )
```

### Глобальный обработчик ошибок

```python
# app/core/middleware.py

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Обработчик ошибок приложения."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
```

### Использование в модулях

```python
# app/modules/new_module/exceptions.py

from app.core.exceptions import NotFoundError


class NewEntityNotFoundError(NotFoundError):
    """Сущность не найдена."""

    def __init__(self, entity_id):
        super().__init__("NewEntity", entity_id)
```

## Логирование

### Конфигурация логирования

```python
# app/core/logging.py

import logging
import sys
from typing import Any

import structlog


def setup_logging(log_level: str = "INFO", json_logs: bool = False):
    """Настройка структурированного логирования."""

    # Настройка structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### Использование

```python
import structlog

logger = structlog.get_logger()

# В коде
logger.info("Операция выполнена", user_id=user_id, action="create")
logger.warning("Подозрительная активность", ip=request.client.host)
logger.error("Ошибка обработки", error=str(exc), exc_info=True)
```

### Контекстное логирование

```python
# Middleware для добавления request_id
from uuid import uuid4
import structlog

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = str(uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

## Тестирование

### Запуск тестов

```bash
cd backend

# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Только unit-тесты
pytest tests/unit

# Только интеграционные
pytest tests/integration

# Конкретный файл
pytest tests/unit/test_auth_service.py

# По маркеру
pytest -m "slow"

# Параллельное выполнение
pytest -n auto
```

### Структура тестов

```python
# tests/unit/test_new_module_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.new_module.service import NewEntityService
from app.modules.new_module.schemas import NewEntityCreate
from app.modules.new_module.exceptions import NewEntityNotFoundError


class TestNewEntityService:
    """Тесты сервиса NewEntity."""

    @pytest.fixture
    def mock_repository(self):
        """Мок репозитория."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Инстанс сервиса с моками."""
        return NewEntityService(repository=mock_repository)

    async def test_create_entity_success(self, service, mock_repository):
        """Успешное создание сущности."""
        # Arrange
        mock_repository.create.return_value = MagicMock(
            id="123",
            name="Test",
            organization_id=1,
        )
        data = NewEntityCreate(name="Test")

        # Act
        result = await service.create(organization_id=1, data=data)

        # Assert
        assert result.name == "Test"
        mock_repository.create.assert_called_once()

    async def test_get_entity_not_found(self, service, mock_repository):
        """Сущность не найдена."""
        # Arrange
        mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NewEntityNotFoundError):
            await service.get_by_id("non-existent-id")
```

## Полезные команды

### Backend

```bash
# Форматирование кода
ruff format .

# Линтинг
ruff check .

# Проверка типов
mypy app

# Все проверки
make lint
```

### Frontend

```bash
# Форматирование
npm run format

# Линтинг
npm run lint

# Проверка типов
npm run typecheck

# Тесты
npm run test
```

### Docker

```bash
# Пересборка образов
docker compose build

# Логи конкретного сервиса
docker compose logs -f backend

# Выполнение команды в контейнере
docker compose exec backend python -m pytest

# Очистка
docker compose down -v
```

## Отладка

### VS Code конфигурация

`.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.main:app", "--reload"],
            "jinja": true,
            "justMyCode": false
        },
        {
            "name": "Python: Pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v", "${file}"]
        }
    ]
}
```

### Отладка в Docker

```bash
# Запуск с debug-портом
docker compose -f docker-compose.yml -f docker-compose.debug.yml up

# Подключение debugger к порту 5678
```

## FAQ

### Как обновить зависимости?

```bash
# Backend
pip install pip-tools
pip-compile --upgrade pyproject.toml
pip-sync requirements.txt

# Frontend
npm update
npm audit fix
```

### Как добавить новую миграцию с данными?

```python
# migrations/versions/xxx_add_initial_data.py

def upgrade():
    # Используем op.execute для data migration
    op.execute("""
        INSERT INTO roles (name, permissions)
        VALUES ('admin', '["*"]')
    """)

def downgrade():
    op.execute("DELETE FROM roles WHERE name = 'admin'")
```

### Как работать с транзакциями?

```python
# Автоматическая транзакция через dependency
async def create_order(
    db: AsyncSession = Depends(get_db),
    service: OrderService = Depends(get_order_service),
):
    # Транзакция управляется автоматически
    return await service.create_order(...)

# Явное управление
async with db.begin():
    await service.operation1()
    await service.operation2()
    # commit при выходе из контекста
```
