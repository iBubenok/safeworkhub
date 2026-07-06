"""Репозиторий чек-листов."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.repositories.base import BaseRepository
from app.models.checklist import (
    Checklist,
    ChecklistItem,
    ChecklistItemReference,
    ChecklistStatus,
    ChecklistVisibility,
)


class ChecklistRepository(BaseRepository[Checklist]):
    """Репозиторий чек-листов."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Checklist, session)

    async def list_for_org(
        self,
        *,
        organization_id: int,
        statuses: list[ChecklistStatus],
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Checklist], int]:
        """Чек-листы: свои (в заданных статусах) + публичные опубликованные из других организаций."""
        own = and_(Checklist.organization_id == organization_id, Checklist.status.in_(statuses))
        # Публичные из других орг. подмешиваем только когда запрошены опубликованные
        # (чтобы фильтры «Черновики»/«Архив» оставались строго внутри своей организации).
        if ChecklistStatus.PUBLISHED in statuses:
            public = and_(
                Checklist.visibility == ChecklistVisibility.PUBLIC,
                Checklist.status == ChecklistStatus.PUBLISHED,
            )
            conditions = [or_(own, public)]
        else:
            conditions = [own]
        if search:
            pattern = f"%{search}%"
            conditions.append(or_(Checklist.title.ilike(pattern), Checklist.description.ilike(pattern)))

        count_query = select(func.count()).select_from(select(Checklist).where(*conditions).subquery())
        total = await self.session.scalar(count_query) or 0

        query = (
            select(Checklist)
            .where(*conditions)
            .options(selectinload(Checklist.items), joinedload(Checklist.organization))
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
                selectinload(Checklist.items)
                .selectinload(ChecklistItem.references)
                .joinedload(ChecklistItemReference.material),
                joinedload(Checklist.author),
                joinedload(Checklist.updated_by),
                joinedload(Checklist.organization),
            )
            .where(Checklist.id == checklist_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def increment_views(self, checklist_id: UUID) -> None:
        """Увеличить счётчик просмотров, не сдвигая updated_at (просмотр ≠ правка)."""
        stmt = (
            update(Checklist)
            .where(Checklist.id == checklist_id)
            .values(views_count=Checklist.views_count + 1, updated_at=Checklist.updated_at)
        )
        await self.session.execute(stmt)

    async def increment_runs(self, checklist_id: UUID) -> None:
        """Увеличить счётчик использований (запусков проверок), не сдвигая updated_at."""
        stmt = (
            update(Checklist)
            .where(Checklist.id == checklist_id)
            .values(runs_count=Checklist.runs_count + 1, updated_at=Checklist.updated_at)
        )
        await self.session.execute(stmt)
