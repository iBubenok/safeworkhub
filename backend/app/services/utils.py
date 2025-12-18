"""Вспомогательные функции сервисов."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


def utcnow() -> datetime:
    """Текущее время в UTC с таймзоной."""
    return datetime.now(UTC)


async def log_audit(
    session: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    organization_id: int | None,
    user_id: str | None,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Сохранить запись аудита."""
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        organization_id=organization_id,
        user_id=user_id,
        request_id=request_id,
        details=details or {},
    )
    session.add(entry)
    await session.flush()
