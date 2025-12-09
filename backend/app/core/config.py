"""Конфигурация приложения через переменные окружения."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
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
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)

    # API
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: list[str] = ["*"]
    cors_origins: list[str] = ["http://localhost:3000"]

    # База данных
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/safeworkhub"
    )
    database_pool_size: int = 20
    database_pool_overflow: int = 10
    database_echo: bool = False

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Email
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = True
    email_from: str = "noreply@safeworkhub.ru"
    email_from_name: str = "SafeWorkHub"

    # S3/MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "safeworkhub"

    # Ограничения
    max_login_attempts: int = 5
    login_lockout_minutes: int = 30
    max_upload_size_mb: int = 50

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Парсинг CORS origins из строки или списка."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """Проверка режима разработки."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Проверка production-режима."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Получение настроек приложения (кэшируется)."""
    return Settings()


settings = get_settings()
