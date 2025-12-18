"""Базовые исключения приложения."""

from typing import Any


class AppError(Exception):
    """Базовое исключение приложения.

    Все пользовательские исключения должны наследоваться от этого класса.
    """

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Инициализация исключения.

        Args:
            message: Сообщение об ошибке.
            code: Код ошибки для клиента.
            status_code: HTTP-код ответа.
            details: Дополнительные детали ошибки.
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Преобразование в словарь для ответа API."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class NotFoundError(AppError):
    """Ресурс не найден."""

    def __init__(
        self,
        resource: str,
        resource_id: str | int | None = None,
        message: str | None = None,
    ) -> None:
        if message is None:
            message = (
                f"{resource} с ID {resource_id} не найден"
                if resource_id
                else f"{resource} не найден"
            )

        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "id": str(resource_id) if resource_id else None},
        )


class ValidationError(AppError):
    """Ошибка валидации данных."""

    def __init__(
        self,
        message: str = "Ошибка валидации данных",
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": errors or []},
        )


class AuthenticationError(AppError):
    """Ошибка аутентификации."""

    def __init__(self, message: str = "Требуется аутентификация") -> None:
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(AppError):
    """Ошибка авторизации (недостаточно прав)."""

    def __init__(self, message: str = "Доступ запрещён") -> None:
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class ConflictError(AppError):
    """Конфликт данных (дубликат, нарушение ограничений)."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details={"field": field} if field else {},
        )


class RateLimitError(AppError):
    """Превышен лимит запросов."""

    def __init__(
        self,
        message: str = "Превышен лимит запросов",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after} if retry_after else {},
        )


class ExternalServiceError(AppError):
    """Ошибка внешнего сервиса."""

    def __init__(
        self,
        service: str,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message=message or f"Ошибка при обращении к сервису {service}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service},
        )


# Специфичные исключения домена

class UserNotFoundError(NotFoundError):
    """Пользователь не найден."""

    def __init__(self, user_id: str | int | None = None) -> None:
        super().__init__("Пользователь", user_id)


class OrganizationNotFoundError(NotFoundError):
    """Организация не найдена."""

    def __init__(self, organization_id: str | int | None = None) -> None:
        super().__init__("Организация", organization_id)


class EmailAlreadyExistsError(ConflictError):
    """Email уже зарегистрирован."""

    def __init__(self, email: str | None = None) -> None:
        super().__init__(message="Пользователь с таким email уже существует", field="email")
        if email:
            self.details["email"] = email


class InvalidCredentialsError(AuthenticationError):
    """Неверные учётные данные."""

    def __init__(self) -> None:
        super().__init__(message="Неверный email или пароль")


class TokenExpiredError(AuthenticationError):
    """Токен истёк."""

    def __init__(self) -> None:
        super().__init__(message="Срок действия токена истёк")


class SubscriptionExpiredError(AuthorizationError):
    """Подписка истекла."""

    def __init__(self) -> None:
        super().__init__(message="Срок действия подписки истёк")


class UserLimitExceededError(ConflictError):
    """Превышен лимит пользователей по тарифу."""

    def __init__(self, limit: int) -> None:
        super().__init__(
            message=f"Превышен лимит пользователей ({limit}) для текущего тарифа",
        )
