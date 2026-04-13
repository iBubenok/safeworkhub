# SafeWorkHub — Корпоративная SaaS-платформа по охране труда

SafeWorkHub — это современная корпоративная справочно-образовательная система с платной подпиской, предназначенная для комплексного решения задач в области охраны труда.

## Ключевые возможности

- **Аутентификация с ротацией refresh** — httpOnly cookie, защита от повторного использования, access-токены только в памяти
- **Корпоративный контур** — организации, роли `org_owner`/`member`, управление пользователями и их статусами
- **Подписки** — статусы trial/active/blocked, единый guard для защищённых модулей
- **База знаний** — материалы, категории, поиск (FTS), публикация и аудит изменений
- **Обучение (LMS)** — курсы, модули, назначения, обновление прогресса
- **Наблюдаемость** — health/readiness, метрики Prometheus, структурированные логи

## Технологический стек

### Backend
- **Python 3.12** — основной язык разработки
- **FastAPI** — асинхронный веб-фреймворк
- **PostgreSQL 16** — основная СУБД
- **Redis** — кэширование и очереди задач
- **SQLAlchemy 2.0** — ORM
- **Alembic** — миграции БД

### Frontend
- **React 18** — UI-библиотека
- **TypeScript** — типизация
- **Vite** — сборка
- **TanStack Query** — управление серверным состоянием
- **Zustand** — клиентское состояние
- **Tailwind CSS** — стилизация

### Инфраструктура
- **Docker** — контейнеризация
- **Docker Compose** — локальная оркестрация
- **GitHub Actions** — CI/CD

## Быстрый старт

### Требования
- Docker 24+ и Docker Compose 2.20+
- Node.js 20+ (для разработки frontend)
- Python 3.12+ (для разработки backend)

### Запуск через Docker Compose

```bash
git clone https://github.com/iBubenok/safeworkhub.git
cd safeworkhub

cp .env.example .env
make up
docker compose exec backend alembic upgrade head
```

Доступы:
- API: http://localhost:8000/api/v1
- Swagger: http://localhost:8000/docs
- Frontend: http://localhost:3000

### Локальная разработка

```bash
# Backend
# В случае отсутствия ссылки на python используйте python3
python -m venv .venv && source .venv/bin/activate

make install-backend

# Запуск из корня проекта safeworkhub
APP_ENV=development .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend

# Запуск из директории safeworkhub/backend
APP_ENV=development .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
make install-frontend
cd frontend && npm run dev -- --host
```

Полезные команды:
- `make lint` — ruff + eslint/tsc
- `make test` — pytest + vitest
- `make db-migrate` — применить миграции Alembic
    
    Перед запуском alembic миграций, необходимо скопировать файл `.env` *(если его нет, скопируйте из шаблона см. выше)* или создать ссылку на него в директории `backend`
    ```shell
    ln -s ../.env backend/.env
    ```

- `make up` / `make down` — поднять/остановить docker-compose окружение

## Структура проекта

```
safeworkhub/
├── backend/                 # FastAPI, модели, схемы, сервисы, тесты
├── frontend/                # React/Vite, Zustand, TanStack Query, тесты
├── infra/                   # Dockerfile, конфигурации nginx
├── .github/workflows/       # CI/CD на GitHub Actions
├── Makefile                 # Стандартные команды (lint/test/build/up)
├── runbook.md               # Операционное руководство
└── *.md                     # Архитектурные и процессные документы
```

## Документация

- [Архитектура системы](ARCHITECTURE.md) — общее описание архитектуры и технологического стека
- [Требования MVP](mvp-requirements-and-architecture.md) — функциональные требования и границы MVP
- [Руководство разработчика](development-guide.md) — инструкции по разработке
- [Стандарты разработки](development-standards.md) — стандарты кодирования и оформления
- [Принципы разработки](development-style.md) — архитектурные и инженерные практики
- [Архитектура работы с БД](sql-execution-engine-architecture.md) — слой данных и SQL
- [Система тестирования](testing-and-code-quality-system.md) — стратегия тестирования
- [Runbook](runbook.md) — диагностика, миграции, бэкапы/восстановление

## Лицензия

Проприетарное программное обеспечение. Все права защищены.

## Автор

**Yan Bubenok**
- Email: yan@bubenok.com
- Telegram: @iBubenok
- GitHub: @iBubenok
