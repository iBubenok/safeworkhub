"""Репозиторий чек-листов."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.repositories.base import BaseRepository
from app.models.checklist import Checklist, ChecklistItem, ChecklistStatus


class ChecklistRepository(BaseRepository[Checklist]):
    """Репозиторий чек-листов."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Checklist, session)

    async def list_for_org(
        self,
        *,
        organization_id: int,
        statuses: list[ChecklistStatus],
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Checklist], int]:
        """Чек-листы организации с фильтром по статусам (с подгрузкой пунктов для счётчика)."""
        conditions = [Checklist.organization_id == organization_id, Checklist.status.in_(statuses)]

        count_query = select(func.count()).select_from(select(Checklist).where(*conditions).subquery())
        total = await self.session.scalar(count_query) or 0

        query = (
            select(Checklist)
            .where(*conditions)
            .options(selectinload(Checklist.items))
            .order_by(desc(Checklist.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_with_items(self, checklist_id: UUID) -> Checklist | None:
        """Чек-лист с пунктами, ссылками-материалами и автором/редактором."""
        query = (
            select(Checklist)
            .options(
                selectinload(Checklist.items).joinedload(ChecklistItem.reference_material),
                joinedload(Checklist.author),
                joinedload(Checklist.updated_by),
            )
            .where(Checklist.id == checklist_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
