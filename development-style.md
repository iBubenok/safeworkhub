# Принципы и стиль разработки SafeWorkHub

## Философия разработки

### Прагматизм над догматизмом

Мы следуем принципам и паттернам не ради них самих, а ради решения реальных проблем. Если правило или паттерн усложняет код без ощутимой пользы — его можно нарушить с обоснованием.

### Простота над сложностью

> "Простота — это высшая степень изощрённости" — Леонардо да Винчи

Простое решение предпочтительнее сложного. Если решение требует длинного объяснения — вероятно, оно слишком сложное.

### Эволюционная архитектура

Архитектура развивается вместе с системой. Не пытаемся предусмотреть все будущие требования. Проектируем для известных требований, оставляя возможность для изменений.

## Архитектурные принципы

### SOLID

#### Single Responsibility Principle (SRP)
Каждый модуль/класс отвечает за одну область функциональности.

```python
# Плохо: класс делает слишком много
class UserService:
    def create_user(self, data): ...
    def send_email(self, user, template): ...
    def generate_pdf_report(self, user): ...
    def validate_inn(self, inn): ...

# Хорошо: разделение ответственности
class UserService:
    def __init__(
        self,
        repository: UserRepository,
        email_service: EmailService,
    ):
        self.repository = repository
        self.email_service = email_service

    def create_user(self, data: UserCreate) -> User:
        user = self.repository.create(data)
        self.email_service.send_welcome(user)
        return user
```

#### Open/Closed Principle (OCP)
Модули открыты для расширения, закрыты для модификации.

```python
# Плохо: добавление нового типа требует изменения существующего кода
class ReportGenerator:
    def generate(self, report_type: str, data: dict):
        if report_type == "pdf":
            return self._generate_pdf(data)
        elif report_type == "excel":
            return self._generate_excel(data)
        # При добавлении нового типа нужно менять этот метод

# Хорошо: расширение через добавление нового класса
class ReportGenerator(Protocol):
    def generate(self, data: dict) -> bytes: ...

class PdfReportGenerator:
    def generate(self, data: dict) -> bytes: ...

class ExcelReportGenerator:
    def generate(self, data: dict) -> bytes: ...
```

#### Dependency Inversion Principle (DIP)
Зависимости направлены к абстракциям, а не конкретным реализациям.

```python
# Плохо: прямая зависимость от конкретной реализации
class UserService:
    def __init__(self):
        self.repository = PostgresUserRepository()  # Жёсткая связь

# Хорошо: зависимость от абстракции
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository  # Любая реализация
```

### Clean Architecture

Зависимости направлены внутрь. Внутренние слои не знают о внешних.

```
┌────────────────────────────────────────────────────┐
│                    Frameworks                       │
│  (FastAPI, SQLAlchemy, React, External APIs)       │
├────────────────────────────────────────────────────┤
│                Interface Adapters                   │
│  (Controllers, Repositories, Presenters)           │
├────────────────────────────────────────────────────┤
│                  Application                        │
│  (Use Cases, Application Services)                 │
├────────────────────────────────────────────────────┤
│                     Domain                          │
│  (Entities, Value Objects, Domain Services)        │
└────────────────────────────────────────────────────┘
```

### Domain-Driven Design (тактические паттерны)

#### Entities
Объекты с идентичностью, изменяемые во времени.

```python
class User:
    """Пользователь — сущность с уникальным идентификатором."""

    id: UUID
    email: str
    name: str

    def change_email(self, new_email: str) -> None:
        """Изменить email с валидацией бизнес-правил."""
        if not self._is_valid_email(new_email):
            raise InvalidEmailError(new_email)
        self.email = new_email
```

#### Value Objects
Неизменяемые объекты без идентичности, определяемые своими атрибутами.

```python
@dataclass(frozen=True)
class Money:
    """Денежная сумма — value object."""

    amount: Decimal
    currency: str

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise CurrencyMismatchError()
        return Money(self.amount + other.amount, self.currency)
```

#### Aggregates
Кластеры связанных сущностей с единой точкой входа.

```python
class Organization:
    """Организация — агрегат с пользователями и подпиской."""

    id: int
    users: list[OrganizationUser]  # Часть агрегата
    subscription: Subscription      # Часть агрегата

    def add_user(self, user_data: UserCreate) -> OrganizationUser:
        """Добавить пользователя с проверкой лимитов подписки."""
        if len(self.users) >= self.subscription.max_users:
            raise UserLimitExceededError()
        user = OrganizationUser(organization_id=self.id, **user_data)
        self.users.append(user)
        return user
```

## Паттерны проектирования

### Repository Pattern

Абстрагирует доступ к данным от бизнес-логики.

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Базовый репозиторий."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> T | None:
        """Получить сущность по ID."""
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Создать сущность."""
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Обновить сущность."""
        ...

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Удалить сущность."""
        ...


class SqlAlchemyUserRepository(Repository[User]):
    """SQLAlchemy-реализация репозитория пользователей."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> User | None:
        return await self.session.get(User, id)

    # ...
```

### Service Layer

Координирует выполнение бизнес-операций.

```python
class OrderService:
    """Сервис для работы с заказами."""

    def __init__(
        self,
        order_repository: OrderRepository,
        payment_service: PaymentService,
        notification_service: NotificationService,
    ):
        self.orders = order_repository
        self.payments = payment_service
        self.notifications = notification_service

    async def create_order(self, data: OrderCreate) -> Order:
        """Создать заказ с обработкой оплаты и уведомлением."""
        # Бизнес-логика координации
        order = await self.orders.create(data)

        try:
            await self.payments.process(order)
        except PaymentError:
            await self.orders.update_status(order.id, OrderStatus.PAYMENT_FAILED)
            raise

        await self.notifications.send_order_confirmation(order)
        return order
```

### Unit of Work

Управляет транзакциями и консистентностью данных.

```python
class UnitOfWork:
    """Единица работы для управления транзакциями."""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self.session_factory()
        self.users = UserRepository(self.session)
        self.orders = OrderRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()


# Использование
async with UnitOfWork(session_factory) as uow:
    user = await uow.users.create(user_data)
    order = await uow.orders.create(order_data)
    # Автоматический commit при выходе
```

### Dependency Injection

В FastAPI используем встроенную систему зависимостей.

```python
# dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
) -> UserService:
    return UserService(repository, email_service)


# router.py
@router.post("/users")
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return await service.create_user(data)
```

## Подходы к рефакторингу

### Правило бойскаута

> "Оставь код чище, чем он был до тебя"

При работе с кодом делаем небольшие улучшения: переименование, удаление дублирования, упрощение логики.

### Рефакторинг в безопасной зоне

1. Убедиться, что есть тесты
2. Делать маленькие шаги
3. Запускать тесты после каждого изменения
4. Коммитить рабочее состояние

### Техники рефакторинга

#### Extract Method
Выделение логики в отдельный метод.

```python
# До
def process_order(order):
    # Валидация
    if not order.items:
        raise ValueError("Order must have items")
    if order.total <= 0:
        raise ValueError("Order total must be positive")

    # Расчёт скидки
    discount = 0
    if order.total > 10000:
        discount = order.total * 0.1
    elif order.total > 5000:
        discount = order.total * 0.05

    # Сохранение
    order.discount = discount
    order.final_total = order.total - discount
    db.save(order)

# После
def process_order(order):
    validate_order(order)
    order.discount = calculate_discount(order.total)
    order.final_total = order.total - order.discount
    db.save(order)

def validate_order(order):
    if not order.items:
        raise ValueError("Order must have items")
    if order.total <= 0:
        raise ValueError("Order total must be positive")

def calculate_discount(total: Decimal) -> Decimal:
    if total > 10000:
        return total * Decimal("0.1")
    if total > 5000:
        return total * Decimal("0.05")
    return Decimal("0")
```

#### Replace Conditional with Polymorphism
Замена условных операторов на полиморфизм.

```python
# До
def calculate_shipping(order):
    if order.shipping_type == "standard":
        return order.weight * 10
    elif order.shipping_type == "express":
        return order.weight * 25 + 200
    elif order.shipping_type == "overnight":
        return order.weight * 50 + 500

# После
class ShippingStrategy(Protocol):
    def calculate(self, order: Order) -> Decimal: ...

class StandardShipping:
    def calculate(self, order: Order) -> Decimal:
        return order.weight * 10

class ExpressShipping:
    def calculate(self, order: Order) -> Decimal:
        return order.weight * 25 + 200

class OvernightShipping:
    def calculate(self, order: Order) -> Decimal:
        return order.weight * 50 + 500

# Использование
shipping_strategies = {
    "standard": StandardShipping(),
    "express": ExpressShipping(),
    "overnight": OvernightShipping(),
}

def calculate_shipping(order):
    strategy = shipping_strategies[order.shipping_type]
    return strategy.calculate(order)
```

## Расширение системы

### Добавление нового модуля

1. Создать структуру каталогов (см. `development-guide.md`)
2. Определить доменные модели
3. Создать Pydantic-схемы
4. Реализовать репозиторий
5. Реализовать сервис
6. Создать API-эндпоинты
7. Написать тесты
8. Зарегистрировать роутер

### Добавление новой интеграции

1. Создать абстракцию (Protocol/ABC)
2. Реализовать конкретный адаптер
3. Добавить конфигурацию
4. Зарегистрировать в DI-контейнере
5. Покрыть тестами (unit + интеграционные)

```python
# 1. Абстракция
class PaymentGateway(Protocol):
    async def charge(self, amount: Money, card: CardInfo) -> PaymentResult: ...
    async def refund(self, payment_id: str) -> RefundResult: ...

# 2. Реализация
class StripePaymentGateway:
    def __init__(self, api_key: str):
        self.client = stripe.Client(api_key)

    async def charge(self, amount: Money, card: CardInfo) -> PaymentResult:
        # Реализация для Stripe
        ...

# 3. Конфигурация
class PaymentSettings(BaseSettings):
    provider: str = "stripe"
    stripe_api_key: SecretStr

# 4. DI-регистрация
def get_payment_gateway(settings: PaymentSettings = Depends(get_settings)):
    if settings.provider == "stripe":
        return StripePaymentGateway(settings.stripe_api_key.get_secret_value())
    raise ValueError(f"Unknown payment provider: {settings.provider}")
```

### Изменение существующей функциональности

1. Написать тесты для текущего поведения (если их нет)
2. Сделать изменения
3. Убедиться, что тесты проходят
4. Добавить тесты для нового поведения
5. Обновить документацию

## Работа с легаси-кодом

### Strangler Fig Pattern

Постепенная замена старого кода новым.

1. Новая функциональность пишется в новом стиле
2. Старый код оборачивается в адаптеры
3. Постепенно переносим логику в новый код
4. Удаляем старый код, когда он не используется

### Characterization Tests

Тесты, которые фиксируют текущее поведение системы.

```python
def test_legacy_calculate_tax_characterization():
    """Характеризационный тест: фиксируем текущее поведение."""
    # Этот тест документирует, как работает legacy-код
    # НЕ проверяет, правильно ли это, а фиксирует факт

    result = legacy_calculate_tax(1000)
    assert result == 180  # Текущее значение, не обязательно правильное

    result = legacy_calculate_tax(500)
    assert result == 80  # Возможно, здесь баг, но это текущее поведение
```

## Антипаттерны (чего избегать)

### God Object
Класс, который знает и делает слишком много.

### Anemic Domain Model
Модели без поведения, вся логика в сервисах.

### Shotgun Surgery
Изменение одной функциональности требует правок во многих местах.

### Feature Envy
Метод больше интересуется данными другого класса, чем своего.

### Premature Optimization
Оптимизация без измерений и реальной необходимости.

### Copy-Paste Programming
Дублирование кода вместо абстрагирования.

## Принятие решений

### Checklist для архитектурных решений

- [ ] Решение соответствует бизнес-требованиям?
- [ ] Учтены ограничения (время, ресурсы, экспертиза)?
- [ ] Рассмотрены альтернативы?
- [ ] Оценены компромиссы?
- [ ] Решение обратимо? Какой ценой?
- [ ] Команда может поддерживать это решение?
- [ ] Решение задокументировано?

### ADR (Architecture Decision Record)

Для значимых решений создаём ADR в `docs/adr/`.

```markdown
# ADR-001: Выбор модульного монолита

## Контекст
Нужно выбрать архитектурный стиль для MVP.

## Решение
Используем модульный монолит с чёткими границами модулей.

## Последствия
+ Простота разработки и деплоя
+ Меньше инфраструктурной сложности
- Требует дисциплины для поддержания границ

## Альтернативы
- Микросервисы: отклонено из-за сложности для MVP
- Монолит без модулей: отклонено из-за рисков связанности
```
