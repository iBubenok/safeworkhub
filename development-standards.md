# Стандарты разработки SafeWorkHub

## Общие принципы

1. **Читаемость важнее краткости** — код читается чаще, чем пишется
2. **Явное лучше неявного** — избегать магии и неочевидного поведения
3. **Консистентность** — следовать установленным паттернам проекта
4. **Минимальная сложность** — простое решение предпочтительнее сложного

## Стандарты кодирования

### Python (Backend)

#### Форматирование

- **Форматтер**: Ruff (совместим с Black)
- **Длина строки**: 100 символов
- **Отступы**: 4 пробела

#### Линтинг

- **Линтер**: Ruff
- **Правила**: pyproject.toml содержит полную конфигурацию

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
]
```

#### Типизация

- **Обязательна** для всех публичных функций и методов
- **Проверка**: mypy в strict mode
- Использовать современный синтаксис (Python 3.12+):
  ```python
  # Правильно
  def get_users(limit: int | None = None) -> list[User]:
      ...

  # Неправильно (устаревший синтаксис)
  def get_users(limit: Optional[int] = None) -> List[User]:
      ...
  ```

#### Именование

| Элемент | Стиль | Пример |
|---------|-------|--------|
| Модули | snake_case | `user_service.py` |
| Классы | PascalCase | `UserService` |
| Функции/методы | snake_case | `get_user_by_id` |
| Переменные | snake_case | `user_count` |
| Константы | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Приватные | _snake_case | `_internal_method` |

#### Документирование

```python
def create_user(
    organization_id: int,
    user_data: UserCreate,
    *,
    send_notification: bool = True,
) -> User:
    """Создание нового пользователя в организации.

    Создаёт учётную запись пользователя, отправляет приглашение
    на указанный email и логирует событие.

    Args:
        organization_id: Идентификатор организации.
        user_data: Данные для создания пользователя.
        send_notification: Отправлять ли email-уведомление.

    Returns:
        Созданный объект пользователя.

    Raises:
        UserAlreadyExistsError: Пользователь с таким email уже существует.
        OrganizationNotFoundError: Организация не найдена.

    Example:
        >>> user = await create_user(1, UserCreate(email="test@example.com"))
        >>> print(user.id)
        123
    """
```

#### Структура модуля

```python
"""Краткое описание модуля.

Развёрнутое описание назначения и использования модуля,
если необходимо.
"""

# Стандартная библиотека
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

# Сторонние библиотеки
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Локальные импорты
from app.core.config import settings
from app.db.session import get_db

if TYPE_CHECKING:
    from app.models import User


# Константы
DEFAULT_PAGE_SIZE = 20


# Классы и функции
class UserService:
    """Сервис для работы с пользователями."""

    ...
```

### TypeScript (Frontend)

#### Форматирование

- **Форматтер**: Prettier
- **Длина строки**: 100 символов
- **Отступы**: 2 пробела
- **Кавычки**: одинарные

#### Линтинг

- **Линтер**: ESLint с TypeScript-плагинами
- **Конфигурация**: `.eslintrc.js`

#### Типизация

- **Strict mode**: обязательно
- Избегать `any`, использовать `unknown` при необходимости
- Экспортировать типы отдельно: `export type { User }`

```typescript
// Правильно
interface User {
  id: string;
  email: string;
  name: string | null;
}

// Неправильно (type для объектов без union/intersection)
type User = {
  id: string;
  email: string;
  name: string | null;
};
```

#### Именование

| Элемент | Стиль | Пример |
|---------|-------|--------|
| Файлы компонентов | PascalCase | `UserProfile.tsx` |
| Файлы утилит | camelCase | `formatDate.ts` |
| Компоненты | PascalCase | `UserProfile` |
| Хуки | camelCase с use- | `useUserData` |
| Функции | camelCase | `formatDate` |
| Переменные | camelCase | `userData` |
| Константы | SCREAMING_SNAKE_CASE | `API_BASE_URL` |
| Типы/интерфейсы | PascalCase | `UserResponse` |
| Enum | PascalCase | `UserRole` |

#### Структура компонента

```tsx
// UserProfile.tsx

// Импорты
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

import { Button } from '@/components/common/Button';
import { useAuth } from '@/hooks/useAuth';
import type { User } from '@/types/user';
import { formatDate } from '@/utils/formatDate';

// Типы (если локальные)
interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
}

// Компонент
export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  // Хуки
  const { user: currentUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  });

  // Эффекты
  useEffect(() => {
    // ...
  }, [userId]);

  // Обработчики
  const handleEdit = () => {
    setIsEditing(true);
  };

  // Условный рендеринг
  if (isLoading) {
    return <Skeleton />;
  }

  // JSX
  return (
    <div className="user-profile">
      {/* ... */}
    </div>
  );
}
```

## Структура файлов и каталогов

### Backend

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Точка входа FastAPI
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py        # Главный роутер
│   │       └── endpoints/       # По одному файлу на ресурс
│   │           ├── auth.py
│   │           └── users.py
│   ├── core/
│   │   ├── config.py            # Pydantic Settings
│   │   ├── security.py          # JWT, хэширование
│   │   └── exceptions.py        # Базовые исключения
│   ├── db/
│   │   ├── base.py              # Базовые классы моделей
│   │   ├── session.py           # AsyncSession factory
│   │   ├── migrations/          # Alembic миграции
│   │   └── repositories/        # Паттерн Repository
│   ├── models/                  # SQLAlchemy модели
│   │   ├── __init__.py          # Re-export всех моделей
│   │   ├── user.py
│   │   └── organization.py
│   ├── schemas/                 # Pydantic схемы
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── common.py            # Общие схемы (pagination)
│   ├── services/                # Бизнес-логика
│   │   ├── user_service.py
│   │   └── auth_service.py
│   └── tasks/                   # Celery задачи
│       └── email_tasks.py
└── tests/
    ├── conftest.py              # Pytest fixtures
    ├── unit/
    └── integration/
```

### Frontend

```
frontend/
├── src/
│   ├── main.tsx                 # Точка входа
│   ├── App.tsx                  # Корневой компонент
│   ├── api/
│   │   ├── client.ts            # Axios/fetch instance
│   │   ├── users.ts             # API-методы по доменам
│   │   └── auth.ts
│   ├── components/
│   │   ├── common/              # Переиспользуемые
│   │   │   ├── Button/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Button.test.tsx
│   │   │   │   └── index.ts
│   │   │   └── Input/
│   │   ├── features/            # По фичам
│   │   │   └── UserProfile/
│   │   └── layouts/             # Layout-компоненты
│   │       └── MainLayout.tsx
│   ├── hooks/                   # Кастомные хуки
│   │   ├── useAuth.ts
│   │   └── useDebounce.ts
│   ├── pages/                   # Страницы (роуты)
│   │   ├── HomePage.tsx
│   │   └── users/
│   │       ├── UserListPage.tsx
│   │       └── UserDetailPage.tsx
│   ├── store/                   # Глобальное состояние
│   │   └── authStore.ts
│   ├── types/                   # TypeScript типы
│   │   ├── user.ts
│   │   └── api.ts
│   └── utils/                   # Утилиты
│       ├── formatDate.ts
│       └── validation.ts
└── tests/
```

## Работа с Git

### Именование веток

```
<тип>/<номер-задачи>-<краткое-описание>

Типы:
- feature/   — новая функциональность
- fix/       — исправление бага
- refactor/  — рефакторинг без изменения поведения
- docs/      — документация
- test/      — тесты
- chore/     — инфраструктурные изменения

Примеры:
feature/123-user-registration
fix/456-login-validation
refactor/789-auth-service
```

### Формат коммитов

Используем Conventional Commits:

```
<тип>(<область>): <описание>

[тело]

[футер]
```

**Типы коммитов:**
- `feat` — новая функциональность
- `fix` — исправление бага
- `docs` — изменения документации
- `style` — форматирование (не влияет на код)
- `refactor` — рефакторинг
- `test` — добавление/изменение тестов
- `chore` — инфраструктура, зависимости

**Примеры:**

```
feat(auth): добавлена регистрация пользователей

Реализована регистрация организаций с автоматическим
созданием администратора. Включает:
- Валидацию ИНН и email
- Отправку confirmation email
- Создание пробного периода

Closes #123
```

```
fix(api): исправлена валидация email при регистрации

Email без домена верхнего уровня теперь корректно отклоняется.

Fixes #456
```

### Правила для коммитов

1. Один коммит = одно логическое изменение
2. Описание на русском языке
3. Первая строка — до 72 символов
4. Тело коммита — wrap на 100 символов
5. Ссылка на задачу в футере

### Merge Request / Pull Request

**Заголовок**: `[<тип>] <краткое описание>`

**Шаблон описания**:

```markdown
## Описание
Краткое описание изменений.

## Тип изменений
- [ ] Новая функциональность
- [ ] Исправление бага
- [ ] Рефакторинг
- [ ] Документация
- [ ] Другое

## Чек-лист
- [ ] Код соответствует стандартам проекта
- [ ] Добавлены/обновлены тесты
- [ ] Документация обновлена
- [ ] Все тесты проходят
- [ ] Нет конфликтов с целевой веткой

## Связанные задачи
Closes #<номер>

## Скриншоты (если применимо)
```

## API Design

### Версионирование

- Версия в URL: `/api/v1/...`
- Major-версия при breaking changes
- Поддержка N-1 версий

### Именование эндпоинтов

```
# Коллекции — множественное число
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{id}
PATCH  /api/v1/users/{id}
DELETE /api/v1/users/{id}

# Вложенные ресурсы
GET    /api/v1/organizations/{org_id}/users
POST   /api/v1/organizations/{org_id}/users

# Действия (RPC-style) — глаголы
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/users/{id}/activate
POST   /api/v1/users/{id}/send-invite
```

### Формат ответов

**Успешный ответ (единичный объект):**
```json
{
  "id": "123",
  "email": "user@example.com",
  "name": "Имя пользователя",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Успешный ответ (коллекция с пагинацией):**
```json
{
  "items": [
    {"id": "1", "name": "..."},
    {"id": "2", "name": "..."}
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

**Ответ с ошибкой:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Ошибка валидации данных",
    "details": {
      "errors": [
        {
          "field": "email",
          "message": "Некорректный формат email"
        }
      ]
    }
  }
}
```

### HTTP-коды ответов

| Код | Использование |
|-----|---------------|
| 200 | Успешный GET, PATCH |
| 201 | Успешный POST (создание) |
| 204 | Успешный DELETE |
| 400 | Некорректный запрос |
| 401 | Требуется аутентификация |
| 403 | Доступ запрещён |
| 404 | Ресурс не найден |
| 409 | Конфликт (дубликат и т.п.) |
| 422 | Ошибка валидации |
| 429 | Превышен лимит запросов |
| 500 | Внутренняя ошибка сервера |

## Документирование

### Код

- Docstrings для публичных функций, классов, модулей
- Inline-комментарии только для неочевидной логики
- README в каждом значимом модуле

### API

- OpenAPI (Swagger) генерируется автоматически из FastAPI
- Описания для каждого эндпоинта
- Примеры запросов и ответов

### Архитектурные решения

- ADR (Architecture Decision Records) для значимых решений
- Формат: `docs/adr/NNNN-название-решения.md`

**Шаблон ADR:**

```markdown
# ADR-NNNN: Название решения

## Статус
Принято | Отклонено | Заменено ADR-XXXX

## Контекст
Описание ситуации и проблемы.

## Решение
Принятое решение.

## Последствия
Положительные и отрицательные последствия решения.

## Альтернативы
Рассмотренные, но отклонённые варианты.
```

## Безопасность

### Обязательные практики

1. **Никогда** не коммитить секреты (пароли, ключи, токены)
2. Использовать переменные окружения для конфигурации
3. Валидировать все входные данные
4. Параметризовать SQL-запросы (ORM делает это автоматически)
5. Экранировать вывод (React делает это автоматически)
6. Использовать HTTPS везде

### Проверки перед коммитом

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

## Производительность

### Backend

1. Использовать асинхронные операции для I/O
2. Добавлять индексы для часто используемых запросов
3. Кэшировать результаты тяжёлых операций
4. Использовать пагинацию для списков
5. Избегать N+1 запросов (eager loading)

### Frontend

1. Ленивая загрузка страниц и крупных компонентов
2. Мемоизация вычислений (`useMemo`, `useCallback`)
3. Виртуализация длинных списков
4. Оптимизация изображений
5. Минимизация бандла (tree-shaking)

## Чек-лист код-ревью

### Общее
- [ ] Код решает поставленную задачу
- [ ] Нет избыточной сложности
- [ ] Соблюдены стандарты кодирования
- [ ] Нет дублирования кода

### Качество
- [ ] Добавлены тесты для новой функциональности
- [ ] Существующие тесты проходят
- [ ] Обработаны ошибки и граничные случаи
- [ ] Нет утечек памяти и ресурсов

### Безопасность
- [ ] Входные данные валидируются
- [ ] Нет SQL-инъекций, XSS и других уязвимостей
- [ ] Секреты не захардкожены
- [ ] Проверены права доступа

### Производительность
- [ ] Нет очевидных проблем производительности
- [ ] Используется кэширование где уместно
- [ ] Нет N+1 запросов к БД

### Документация
- [ ] Код самодокументирован или добавлены комментарии
- [ ] API документировано
- [ ] README обновлён при необходимости
