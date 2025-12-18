"""Конфигурация приложения через переменные окружения."""

from functools import lru_cache
from typing import Literal, cast

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения.

    Загружаются из переменных окружения с поддержкой .env файла.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Общие настройки
    app_name: str = "SafeWorkHub"
    app_env: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"

    # Безопасность
    secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    refresh_token_cookie_name: str = "swh_refresh_token"
    refresh_token_secure: bool = False
    refresh_token_domain: str | None = None
    refresh_token_samesite: Literal["lax", "strict", "none"] = "lax"
    max_login_attempts: int = 5
    login_lockout_minutes: int = 30

    # API
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Список хостов, откуда разрешены запросы",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    # База данных
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/safeworkhub"
    )
    database_pool_size: int = 20
    database_pool_overflow: int = 10
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Подписки
    subscription_trial_days: int = 14
    default_tariff_code: str = "base"

    # Наблюдаемость
    prometheus_enabled: bool = True
    metrics_namespace: str = "safeworkhub"
    request_timeout_seconds: int = 30

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def parse_list(cls, value: str | list[str]) -> list[str]:
        """Парсинг списков из строки с разделителем запятая."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("refresh_token_samesite", mode="before")
    @classmethod
    def normalize_samesite(cls, value: str) -> Literal["lax", "strict", "none"]:
        """Нормализует значение SameSite для cookie refresh-токена."""
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("refresh_token_samesite должен быть lax, strict или none")
        return cast("Literal['lax', 'strict', 'none']", normalized)

    @property
    def is_development(self) -> bool:
        """Проверка режима разработки."""
        return self.app_env == "development"

    @property
    def is_testing(self) -> bool:
        """Проверка режима тестирования."""
        return self.app_env == "testing"

    @property
    def is_production(self) -> bool:
        """Проверка production-режима."""
        return self.app_env == "production"

    @property
    def refresh_cookie_path(self) -> str:
        """Путь cookie для refresh-токена."""
        return f"{self.api_v1_prefix}/auth"

    @property
    def refresh_cookie_secure(self) -> bool:
        """Secure для refresh-cookie: принудительно включается в production."""
        return self.refresh_token_secure or self.is_production


@lru_cache
def get_settings() -> Settings:
    """Получение настроек приложения (кэшируется)."""
    return Settings()


settings = get_settings()
