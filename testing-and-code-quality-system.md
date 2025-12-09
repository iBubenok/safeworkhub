# Система тестирования и контроля качества кода

## Обзор

Документ описывает стратегию тестирования SafeWorkHub, используемые инструменты и практики обеспечения качества кода.

## Пирамида тестирования

```
                    ┌─────────┐
                    │   E2E   │     5%
                    │  Tests  │
                    ├─────────┤
                   /           \
                  /  Integration \   20%
                 /     Tests      \
                ├─────────────────┤
               /                   \
              /     Unit Tests      \   75%
             /                       \
            └─────────────────────────┘
```

| Уровень | Покрытие | Скорость | Фокус |
|---------|----------|----------|-------|
| Unit | 75% тестов | Быстро (мс) | Отдельные функции, классы |
| Integration | 20% тестов | Средне (сек) | Взаимодействие компонентов |
| E2E | 5% тестов | Медленно (мин) | Пользовательские сценарии |

## Инструменты

### Backend

| Инструмент | Назначение |
|------------|------------|
| **pytest** | Фреймворк тестирования |
| **pytest-asyncio** | Поддержка async-тестов |
| **pytest-cov** | Покрытие кода |
| **pytest-xdist** | Параллельное выполнение |
| **factory-boy** | Фабрики тестовых данных |
| **httpx** | Асинхронный HTTP-клиент для тестов API |
| **Faker** | Генерация фейковых данных |
| **freezegun** | Мокирование времени |

### Frontend

| Инструмент | Назначение |
|------------|------------|
| **Vitest** | Фреймворк тестирования |
| **React Testing Library** | Тестирование React-компонентов |
| **MSW (Mock Service Worker)** | Мокирование API |
| **Playwright** | E2E-тестирование |

### Статический анализ

| Инструмент | Назначение |
|------------|------------|
| **Ruff** | Линтер и форматтер Python |
| **mypy** | Проверка типов Python |
| **ESLint** | Линтер TypeScript/JavaScript |
| **Prettier** | Форматтер TypeScript/JavaScript |
| **TypeScript** | Проверка типов |

## Конфигурация

### pytest (backend)

```toml
# pyproject.toml

[tool.pytest.ini_options]
minversion = "8.0"
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "-ra",
]
markers = [
    "slow: медленные тесты (> 1 сек)",
    "integration: интеграционные тесты",
    "e2e: end-to-end тесты",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["app"]
branch = true
omit = [
    "*/migrations/*",
    "*/__init__.py",
    "*/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@abstractmethod",
]
fail_under = 70
show_missing = true
```

### Vitest (frontend)

```typescript
// vite.config.ts

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
      ],
      thresholds: {
        statements: 70,
        branches: 70,
        functions: 70,
        lines: 70,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

## Unit-тесты

### Backend: структура теста

```python
# tests/unit/services/test_user_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.models import User
from app.core.exceptions import UserNotFoundError, EmailAlreadyExistsError


class TestUserService:
    """Тесты сервиса пользователей."""

    @pytest.fixture
    def mock_repository(self):
        """Мок репозитория."""
        return AsyncMock()

    @pytest.fixture
    def mock_email_service(self):
        """Мок email-сервиса."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repository, mock_email_service):
        """Инстанс сервиса с моками."""
        return UserService(
            repository=mock_repository,
            email_service=mock_email_service,
        )

    @pytest.fixture
    def sample_user(self):
        """Пример пользователя."""
        return User(
            id=uuid4(),
            email="test@example.com",
            name="Тестовый пользователь",
            is_active=True,
        )

    # --- Тесты создания ---

    async def test_create_user_success(
        self,
        service,
        mock_repository,
        mock_email_service,
        sample_user,
    ):
        """Успешное создание пользователя."""
        # Arrange
        create_data = UserCreate(
            email="new@example.com",
            password="SecureP@ss123",
            name="Новый пользователь",
        )
        mock_repository.get_by_email.return_value = None
        mock_repository.create.return_value = sample_user

        # Act
        result = await service.create_user(organization_id=1, data=create_data)

        # Assert
        assert result.email == sample_user.email
        mock_repository.create.assert_called_once()
        mock_email_service.send_welcome_email.assert_called_once_with(sample_user)

    async def test_create_user_email_exists(
        self,
        service,
        mock_repository,
        sample_user,
    ):
        """Ошибка при существующем email."""
        # Arrange
        create_data = UserCreate(
            email="existing@example.com",
            password="SecureP@ss123",
            name="Тест",
        )
        mock_repository.get_by_email.return_value = sample_user

        # Act & Assert
        with pytest.raises(EmailAlreadyExistsError):
            await service.create_user(organization_id=1, data=create_data)

        mock_repository.create.assert_not_called()

    # --- Тесты получения ---

    async def test_get_user_success(self, service, mock_repository, sample_user):
        """Успешное получение пользователя."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_user

        # Act
        result = await service.get_user(sample_user.id)

        # Assert
        assert result.id == sample_user.id
        mock_repository.get_by_id.assert_called_once_with(sample_user.id)

    async def test_get_user_not_found(self, service, mock_repository):
        """Пользователь не найден."""
        # Arrange
        user_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await service.get_user(user_id)

    # --- Параметризованные тесты ---

    @pytest.mark.parametrize(
        "email,is_valid",
        [
            ("valid@example.com", True),
            ("user.name@domain.co.uk", True),
            ("invalid", False),
            ("@nodomain.com", False),
            ("spaces in@email.com", False),
        ],
    )
    async def test_email_validation(self, service, email, is_valid):
        """Валидация email-адресов."""
        result = service.validate_email(email)
        assert result == is_valid
```

### Frontend: тестирование компонентов

```typescript
// src/components/features/UserProfile/UserProfile.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { UserProfile } from './UserProfile';
import * as userApi from '@/api/users';

// Мокирование API
vi.mock('@/api/users');

const mockUser = {
  id: '123',
  email: 'test@example.com',
  name: 'Тестовый пользователь',
  role: 'specialist',
};

describe('UserProfile', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  const renderComponent = (userId = '123') => {
    return render(
      <QueryClientProvider client={queryClient}>
        <UserProfile userId={userId} />
      </QueryClientProvider>
    );
  };

  it('отображает загрузку при получении данных', () => {
    vi.mocked(userApi.getUser).mockImplementation(
      () => new Promise(() => {}) // Бесконечный pending
    );

    renderComponent();

    expect(screen.getByTestId('user-profile-skeleton')).toBeInTheDocument();
  });

  it('отображает данные пользователя', async () => {
    vi.mocked(userApi.getUser).mockResolvedValue(mockUser);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    });
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  it('отображает ошибку при неудачном запросе', async () => {
    vi.mocked(userApi.getUser).mockRejectedValue(new Error('Ошибка сети'));

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/ошибка загрузки/i)).toBeInTheDocument();
    });
  });

  it('позволяет редактировать имя', async () => {
    const user = userEvent.setup();
    vi.mocked(userApi.getUser).mockResolvedValue(mockUser);
    vi.mocked(userApi.updateUser).mockResolvedValue({
      ...mockUser,
      name: 'Новое имя',
    });

    renderComponent();

    // Ждём загрузку
    await waitFor(() => {
      expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    });

    // Открываем редактирование
    await user.click(screen.getByRole('button', { name: /редактировать/i }));

    // Изменяем имя
    const nameInput = screen.getByLabelText(/имя/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'Новое имя');

    // Сохраняем
    await user.click(screen.getByRole('button', { name: /сохранить/i }));

    await waitFor(() => {
      expect(userApi.updateUser).toHaveBeenCalledWith('123', {
        name: 'Новое имя',
      });
    });
  });
});
```

### Frontend: тестирование хуков

```typescript
// src/hooks/useAuth.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useAuth } from './useAuth';
import * as authApi from '@/api/auth';

vi.mock('@/api/auth');

describe('useAuth', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
    localStorage.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('возвращает isAuthenticated: false для неавторизованного пользователя', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('выполняет вход и обновляет состояние', async () => {
    const mockUser = { id: '1', email: 'test@example.com', name: 'Тест' };
    const mockTokens = { accessToken: 'token', refreshToken: 'refresh' };

    vi.mocked(authApi.login).mockResolvedValue({
      user: mockUser,
      tokens: mockTokens,
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({
        email: 'test@example.com',
        password: 'password',
      });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(localStorage.getItem('accessToken')).toBe('token');
  });

  it('выполняет выход и очищает состояние', async () => {
    localStorage.setItem('accessToken', 'token');

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('accessToken')).toBeNull();
  });
});
```

## Интеграционные тесты

### Тестирование API (backend)

```python
# tests/integration/api/test_users_api.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from tests.factories import UserFactory, OrganizationFactory


@pytest.mark.integration
class TestUsersAPI:
    """Интеграционные тесты API пользователей."""

    @pytest.fixture
    async def auth_client(
        self,
        client: AsyncClient,
        test_user,
        auth_headers,
    ):
        """Клиент с авторизацией."""
        client.headers.update(auth_headers)
        return client

    async def test_get_current_user(self, auth_client, test_user):
        """Получение текущего пользователя."""
        response = await auth_client.get("/api/v1/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert "password_hash" not in data

    async def test_update_current_user(self, auth_client, test_user):
        """Обновление текущего пользователя."""
        new_name = "Обновлённое имя"

        response = await auth_client.patch(
            "/api/v1/users/me",
            json={"name": new_name},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name

    async def test_list_organization_users(
        self,
        auth_client,
        db_session: AsyncSession,
        test_organization,
    ):
        """Список пользователей организации."""
        # Создаём дополнительных пользователей
        users = UserFactory.create_batch(5)
        for user in users:
            await db_session.execute(
                insert(OrganizationUser).values(
                    organization_id=test_organization.id,
                    user_id=user.id,
                    role_id=1,
                )
            )
        await db_session.commit()

        response = await auth_client.get(
            f"/api/v1/organizations/{test_organization.id}/users"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        assert len(data["items"]) <= 20  # Дефолтный page_size

    async def test_unauthorized_access(self, client: AsyncClient):
        """Запрос без авторизации."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.integration
class TestAuthAPI:
    """Интеграционные тесты API аутентификации."""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Успешная аутентификация."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "test_password",  # Пароль из фикстуры
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Неверный пароль."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Несуществующий пользователь."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password",
            },
        )

        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient, test_user):
        """Обновление токенов."""
        # Сначала логинимся
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "test_password",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Обновляем токен
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
```

### Тестирование БД

```python
# tests/integration/repositories/test_user_repository.py

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import UserRepository
from app.models import User
from tests.factories import UserFactory


@pytest.mark.integration
class TestUserRepository:
    """Интеграционные тесты репозитория пользователей."""

    @pytest.fixture
    def repository(self, db_session: AsyncSession):
        return UserRepository(db_session)

    async def test_create_user(self, repository, db_session):
        """Создание пользователя в БД."""
        user = await repository.create(
            email="new@example.com",
            password_hash="hashed",
            name="Новый",
        )

        assert user.id is not None
        assert user.email == "new@example.com"

        # Проверяем, что сохранено в БД
        db_user = await db_session.get(User, user.id)
        assert db_user is not None
        assert db_user.email == "new@example.com"

    async def test_get_by_email(self, repository, test_user):
        """Поиск по email."""
        user = await repository.get_by_email(test_user.email)

        assert user is not None
        assert user.id == test_user.id

    async def test_get_by_email_not_found(self, repository):
        """Несуществующий email."""
        user = await repository.get_by_email("nonexistent@example.com")

        assert user is None

    async def test_search_users(self, repository, db_session):
        """Поиск пользователей."""
        # Создаём тестовые данные
        await repository.create(
            email="ivan@example.com",
            password_hash="hash",
            name="Иван Петров",
        )
        await repository.create(
            email="petr@example.com",
            password_hash="hash",
            name="Пётр Иванов",
        )
        await db_session.commit()

        # Поиск по имени
        results = await repository.search("Иван")

        assert len(results) == 2  # Иван Петров и Пётр Иванов

    async def test_update_user(self, repository, test_user, db_session):
        """Обновление пользователя."""
        updated = await repository.update(
            test_user.id,
            name="Обновлённое имя",
        )
        await db_session.commit()

        assert updated is not None
        assert updated.name == "Обновлённое имя"

        # Проверяем в БД
        await db_session.refresh(test_user)
        assert test_user.name == "Обновлённое имя"
```

## E2E-тесты

### Playwright (frontend)

```typescript
// tests/e2e/auth.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Аутентификация', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('успешный вход', async ({ page }) => {
    // Заполняем форму
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Пароль').fill('password123');
    await page.getByRole('button', { name: 'Войти' }).click();

    // Проверяем редирект на дашборд
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Добро пожаловать')).toBeVisible();
  });

  test('ошибка при неверном пароле', async ({ page }) => {
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Пароль').fill('wrong_password');
    await page.getByRole('button', { name: 'Войти' }).click();

    await expect(page.getByText('Неверный email или пароль')).toBeVisible();
    await expect(page).toHaveURL('/login');
  });

  test('валидация email', async ({ page }) => {
    await page.getByLabel('Email').fill('invalid-email');
    await page.getByLabel('Пароль').fill('password');
    await page.getByRole('button', { name: 'Войти' }).click();

    await expect(page.getByText('Некорректный email')).toBeVisible();
  });
});

test.describe('Регистрация организации', () => {
  test('полный флоу регистрации', async ({ page }) => {
    await page.goto('/register');

    // Шаг 1: Данные организации
    await page.getByLabel('Название организации').fill('ООО Тест');
    await page.getByLabel('ИНН').fill('7707083893');
    await page.getByRole('button', { name: 'Далее' }).click();

    // Шаг 2: Данные администратора
    await page.getByLabel('Email').fill('admin@test.com');
    await page.getByLabel('Пароль').fill('SecureP@ss123');
    await page.getByLabel('Повторите пароль').fill('SecureP@ss123');
    await page.getByLabel('Имя').fill('Администратор');
    await page.getByRole('button', { name: 'Зарегистрироваться' }).click();

    // Проверяем успешную регистрацию
    await expect(page.getByText('Регистрация завершена')).toBeVisible();
    await expect(
      page.getByText('Письмо для подтверждения отправлено')
    ).toBeVisible();
  });
});
```

### Конфигурация Playwright

```typescript
// playwright.config.ts

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { open: 'never' }]],

  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile',
      use: { ...devices['iPhone 13'] },
    },
  ],

  webServer: {
    command: 'npm run preview',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Фабрики тестовых данных

### Backend: factory-boy

```python
# tests/factories.py

import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

from app.db.session import async_session_factory
from app.models import User, Organization, Course, Material

fake = Faker("ru_RU")


class BaseFactory(SQLAlchemyModelFactory):
    """Базовая фабрика с сессией."""

    class Meta:
        abstract = True
        sqlalchemy_session = None  # Устанавливается в фикстуре
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    """Фабрика пользователей."""

    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    password_hash = factory.LazyAttribute(
        lambda _: "$argon2id$v=19$m=65536,t=3,p=4$..."  # Фейковый хэш
    )
    name = factory.LazyAttribute(lambda _: fake.name())
    is_active = True
    is_superuser = False


class OrganizationFactory(BaseFactory):
    """Фабрика организаций."""

    class Meta:
        model = Organization

    name = factory.LazyAttribute(lambda _: fake.company())
    inn = factory.LazyAttribute(lambda _: fake.businesses_inn())
    description = factory.LazyAttribute(lambda _: fake.catch_phrase())


class CourseFactory(BaseFactory):
    """Фабрика курсов."""

    class Meta:
        model = Course

    title = factory.LazyAttribute(
        lambda _: f"Курс: {fake.catch_phrase()}"
    )
    description = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=500))
    duration_hours = factory.LazyAttribute(lambda _: fake.random_int(4, 40))
    is_published = True


class MaterialFactory(BaseFactory):
    """Фабрика материалов базы знаний."""

    class Meta:
        model = Material

    title = factory.LazyAttribute(lambda _: fake.sentence())
    content = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=2000))
    type = factory.LazyAttribute(
        lambda _: fake.random_element(["article", "npa", "template"])
    )
```

## Fixtures

### conftest.py (backend)

```python
# tests/conftest.py

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from tests.factories import UserFactory, OrganizationFactory


# Тестовая БД
TEST_DATABASE_URL = settings.database_url.replace(
    settings.database_name,
    f"{settings.database_name}_test",
)

engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Создание таблиц перед тестами."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия БД с откатом после теста."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_session(db_session: AsyncSession):
    """Override dependency get_session."""

    async def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_get_session) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент для тестов API."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Тестовый пользователь."""
    UserFactory._meta.sqlalchemy_session = db_session
    user = UserFactory.create(password_hash=get_password_hash("test_password"))
    await db_session.commit()
    return user


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Тестовая организация."""
    OrganizationFactory._meta.sqlalchemy_session = db_session
    org = OrganizationFactory.create()
    await db_session.commit()
    return org


@pytest.fixture
def auth_headers(test_user) -> dict[str, str]:
    """Заголовки авторизации."""
    from app.core.security import create_access_token

    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}
```

## Запуск тестов

### Backend

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Только unit-тесты
pytest tests/unit

# Только интеграционные
pytest -m integration

# Параллельно
pytest -n auto

# Конкретный тест
pytest tests/unit/test_user_service.py::TestUserService::test_create_user_success

# С подробным выводом
pytest -v --tb=long
```

### Frontend

```bash
# Все тесты
npm run test

# Watch-режим
npm run test:watch

# С покрытием
npm run test:coverage

# E2E
npm run test:e2e

# E2E в headed-режиме
npm run test:e2e -- --headed
```

## CI/CD интеграция

```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: safeworkhub_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Run linting
        run: |
          cd backend
          ruff check .
          ruff format --check .

      - name: Run type checking
        run: |
          cd backend
          mypy app

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/safeworkhub_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run linting
        run: |
          cd frontend
          npm run lint
          npm run typecheck

      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Playwright
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps

      - name: Start services
        run: docker compose -f docker-compose.test.yml up -d

      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Метрики качества

### Целевые показатели

| Метрика | Минимум | Цель |
|---------|---------|------|
| Покрытие кода | 70% | 85% |
| Покрытие веток | 60% | 75% |
| Время unit-тестов | < 2 мин | < 1 мин |
| Время CI pipeline | < 15 мин | < 10 мин |
| Flaky tests | < 2% | 0% |

### Мониторинг качества

- **SonarQube** — статический анализ и технический долг
- **Codecov** — отслеживание покрытия
- **Dependabot** — обновление зависимостей
