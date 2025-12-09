# SafeWorkHub — Корпоративная SaaS-платформа по охране труда

SafeWorkHub — это современная корпоративная справочно-образовательная система с платной подпиской, предназначенная для комплексного решения задач в области охраны труда.

## Ключевые возможности

- **База знаний по охране труда** — структурированные экспертные рекомендации, нормативно-правовая база, шаблоны документов
- **Экспертные консультации** — многоуровневая поддержка от специалистов по охране труда
- **Система обучения (LMS)** — онлайн-курсы, тестирование, выдача удостоверений
- **Интерактивные сервисы** — мастера документов, калькуляторы, навигаторы СИЗ
- **Корпоративный контур** — многопользовательский режим, роли и права, хранение внутренних документов

## Технологический стек

### Backend
- **Python 3.12** — основной язык разработки
- **FastAPI** — асинхронный веб-фреймворк
- **PostgreSQL 16** — основная СУБД
- **Redis** — кэширование и очереди задач
- **Celery** — фоновые задачи
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
- Node.js 20+ (для локальной разработки frontend)
- Python 3.12+ (для локальной разработки backend)

### Запуск через Docker Compose

```bash
# Клонирование репозитория
git clone https://github.com/iBubenok/safeworkhub.git
cd safeworkhub

# Копирование конфигурации окружения
cp .env.example .env

# Запуск всех сервисов
docker compose up -d

# Применение миграций БД
docker compose exec backend alembic upgrade head

# Создание начальных данных
docker compose exec backend python -m app.db.init_data
```

После запуска:
- API: http://localhost:8000
- Документация API (Swagger): http://localhost:8000/docs
- Frontend: http://localhost:3000

### Локальная разработка

#### Backend
```bash
cd backend

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Установка зависимостей
pip install -e ".[dev]"

# Запуск сервера разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend

# Установка зависимостей
npm install

# Запуск сервера разработки
npm run dev
```

## Структура проекта

```
repository/
├── backend/                 # Серверная часть
│   ├── app/                 # Исходный код приложения
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Конфигурация и базовые компоненты
│   │   ├── db/              # Работа с БД, миграции
│   │   ├── models/          # SQLAlchemy модели
│   │   ├── schemas/         # Pydantic схемы
│   │   ├── services/        # Бизнес-логика
│   │   └── tasks/           # Celery задачи
│   └── tests/               # Тесты backend
├── frontend/                # Клиентская часть
│   ├── src/                 # Исходный код
│   └── tests/               # Тесты frontend
├── infra/                   # Инфраструктура
│   ├── docker/              # Dockerfile и конфигурации
│   └── ci/                  # CI/CD пайплайны
└── docs/                    # Дополнительная документация
```

## Документация

- [Архитектура системы](ARCHITECTURE.md) — общее описание архитектуры и технологического стека
- [Требования MVP](mvp-requirements-and-architecture.md) — функциональные требования и границы MVP
- [Руководство разработчика](development-guide.md) — инструкции по разработке
- [Стандарты разработки](development-standards.md) — стандарты кодирования и оформления
- [Принципы разработки](development-style.md) — архитектурные и инженерные практики
- [Архитектура работы с БД](sql-execution-engine-architecture.md) — слой данных и SQL
- [Система тестирования](testing-and-code-quality-system.md) — стратегия тестирования

## Лицензия

Проприетарное программное обеспечение. Все права защищены.

## Автор

**Yan Bubenok**
- Email: yan@bubenok.com
- Telegram: @iBubenok
- GitHub: @iBubenok
