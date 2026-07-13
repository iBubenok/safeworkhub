"""Репозиторий для работы с курсами и назначениями."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models import AssignmentStatus, Course, CourseAssignment


class CourseRepository(BaseRepository[Course]):
    """Работа с курсами и их модулями."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Course, session)

    async def list_for_org(
        self,
        organization_id: int,
        *,
        published_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Course]:
        query = (
            select(Course)
            .where(Course.organization_id == organization_id)
            .order_by(Course.title)
            .limit(limit)
            .offset(offset)
        )
        if published_only:
            query = query.where(Course.is_published.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_for_org(self, course_id: int, organization_id: int) -> Course | None:
        query = select(Course).where(Course.id == course_id, Course.organization_id == organization_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class CourseAssignmentRepository(BaseRepository[CourseAssignment]):
    """Работа с назначениями курсов пользователям."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CourseAssignment, session)

    async def get_for_user(
        self,
        course_id: int,
        user_id: UUID,
        organization_id: int,
    ) -> CourseAssignment | None:
        query = select(CourseAssignment).where(
            CourseAssignment.course_id == course_id,
            CourseAssignment.user_id == user_id,
            CourseAssignment.organization_id == organization_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        organization_id: int,
    ) -> list[CourseAssignment]:
        query = select(CourseAssignment).where(
            CourseAssignment.user_id == user_id,
            CourseAssignment.organization_id == organization_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def assign_course(
        self,
        *,
        course_id: int,
        organization_id: int,
        user_id: UUID,
        due_at: datetime | None = None,
    ) -> CourseAssignment:
        assignment = CourseAssignment(
            course_id=course_id,
            organization_id=organization_id,
            user_id=user_id,
            status=AssignmentStatus.ASSIGNED,
            progress_percent=0,
            due_at=due_at,
        )
        self.session.add(assignment)
        await self.session.flush()
        await self.session.refresh(assignment)
        return assignment

    async def update_progress(
        self,
        assignment: CourseAssignment,
        *,
        progress_percent: int,
        status: AssignmentStatus | None = None,
    ) -> CourseAssignment:
        assignment.progress_percent = progress_percent
        assignment.last_activity_at = datetime.now(UTC)
        if status:
            assignment.status = status
            if status == AssignmentStatus.COMPLETED:
                assignment.completed_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(assignment)
        return assignment
