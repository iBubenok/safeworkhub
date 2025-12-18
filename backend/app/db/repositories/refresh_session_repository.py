"""Репозиторий refresh-сессий."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models import RefreshSession


class RefreshSessionRepository(BaseRepository[RefreshSession]):
    """Работа с refresh-сессиями пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RefreshSession, session)

    async def create_session(
        self,
        *,
        session_id: UUID | None = None,
        user_id: UUID,
        family_id: UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
    ) -> RefreshSession:
        session = RefreshSession(
            id=session_id,
            user_id=user_id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            last_used_at=datetime.now(UTC),
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_active(self, session_id: UUID) -> RefreshSession | None:
        """Получить активную (не отозванную) refresh-сессию."""
        query = select(RefreshSession).where(
            RefreshSession.id == session_id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > datetime.now(UTC),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke(self, session_id: UUID, *, replaced_by: UUID | None = None) -> None:
        """Отозвать конкретную refresh-сессию."""
        session = await self.get_by_id(session_id)
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(UTC)
            session.replaced_by = replaced_by
            await self.session.flush()

    async def revoke_family(self, family_id: UUID) -> None:
        """Отозвать все токены семейства (защита от повторного использования)."""
        await self.session.execute(
            update(RefreshSession)
            .where(RefreshSession.family_id == family_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )

    async def mark_used(self, session_id: UUID) -> None:
        """Обновить время последнего использования."""
        session = await self.get_by_id(session_id)
        if session:
            session.last_used_at = datetime.now(UTC)
            await self.session.flush()
