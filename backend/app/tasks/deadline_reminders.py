"""Фоновое напоминание о скором сроке проверки."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.models.checklist_run import ChecklistRun, ChecklistRunStatus
from app.services.checklist_run_service import ChecklistRunService
from app.services.notification_service import NotificationService
from app.services.redis_service import RedisService
from app.services.utils import utcnow

logger = logging.getLogger(__name__)


async def scan_due_deadline_reminders(
    session: AsyncSession,
    notifications: NotificationService,
    *,
    threshold_hours: int,
    now: datetime,
) -> int:
    """Разослать напоминания «скоро срок» и пометить их отправленными. Возвращает число проверок."""
    deadline = now + timedelta(hours=threshold_hours)
    stmt = (
        select(ChecklistRun)
        .options(selectinload(ChecklistRun.assignees))
        .where(
            ChecklistRun.status == ChecklistRunStatus.IN_PROGRESS,
            ChecklistRun.due_at.is_not(None),
            ChecklistRun.due_at > now,
            ChecklistRun.due_at <= deadline,
            ChecklistRun.deadline_reminded_at.is_(None),
        )
    )
    runs = list((await session.execute(stmt)).scalars().all())
    service = ChecklistRunService(session, notifications=notifications)
    for run in runs:
        recipients = service._run_audience(run)
        run.deadline_reminded_at = now
        await session.flush()
        due = run.due_at
        await service._notify(
            run,
            recipients,
            title="Скоро срок проверки",
            message=f"Срок проверки «{run.title or run.checklist_title}» истекает {due:%d.%m.%Y %H:%M}"
            if due
            else f"Срок проверки «{run.title or run.checklist_title}» истекает",
            type_="warning",
            category="reminder",
        )
    await session.commit()
    return len(runs)


async def deadline_reminder_loop() -> None:
    """Периодический скан напоминаний. Свои сессия/Redis; ошибки не роняют цикл."""
    settings = get_settings()
    factory = get_sessionmaker()
    while True:
        try:
            redis_client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
            try:
                async with factory() as session:
                    notifications = NotificationService(session, RedisService(redis_client))
                    await scan_due_deadline_reminders(
                        session,
                        notifications,
                        threshold_hours=settings.deadline_reminder_threshold_hours,
                        now=utcnow(),
                    )
            finally:
                await redis_client.aclose()
        except Exception:
            logger.exception("Сканирование напоминаний о сроке завершилось ошибкой")
        await asyncio.sleep(settings.deadline_reminder_interval_seconds)
