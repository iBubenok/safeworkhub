"""Репозиторий проверок по чек-листам."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.repositories.base import BaseRepository
from app.models.checklist_run import ChecklistRun, ChecklistRunAnswer, ChecklistRunStatus


class ChecklistRunRepository(BaseRepository[ChecklistRun]):
    """Репозиторий проверок."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ChecklistRun, session)

    async def list_for_org(
        self,
        *,
        organization_id: int,
        statuses: list[ChecklistRunStatus] | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ChecklistRun], int]:
        """Проверки организации (с автором, для карточек списка)."""
        conditions = [ChecklistRun.organization_id == organization_id]
        if statuses:
            conditions.append(ChecklistRun.status.in_(statuses))
        if search:
            pattern = f"%{search}%"
            conditions.append(or_(ChecklistRun.title.ilike(pattern), ChecklistRun.checklist_title.ilike(pattern)))

        count_query = select(func.count()).select_from(select(ChecklistRun).where(*conditions).subquery())
        total = await self.session.scalar(count_query) or 0

        query = (
            select(ChecklistRun)
            .where(*conditions)
            .options(
                joinedload(ChecklistRun.conducted_by),
                selectinload(ChecklistRun.assignees),
            )
            .order_by(desc(ChecklistRun.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_with_answers(self, run_id: UUID) -> ChecklistRun | None:
        """Проверка с ответами, автором и данными о корректировках."""
        query = (
            select(ChecklistRun)
            .options(
                selectinload(ChecklistRun.answers).joinedload(ChecklistRunAnswer.corrected_by),
                joinedload(ChecklistRun.conducted_by),
                joinedload(ChecklistRun.corrected_by),
                selectinload(ChecklistRun.assignees),
            )
            .where(ChecklistRun.id == run_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
