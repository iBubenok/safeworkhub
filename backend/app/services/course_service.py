"""Сервис для работы с курсами и назначениями."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.repositories import CourseAssignmentRepository, CourseRepository
from app.models.course import AssignmentStatus, Course
from app.schemas.course import (
    CourseAssignmentResponse,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
)
from app.services.utils import log_audit


class CourseService:
    """Управление курсами и назначениями (вариант A)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.course_repo = CourseRepository(session)
        self.assignment_repo = CourseAssignmentRepository(session)

    async def list_courses(
        self,
        organization_id: int,
        *,
        published_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Course]:
        return await self.course_repo.list_for_org(
            organization_id=organization_id,
            published_only=published_only,
            limit=limit,
            offset=offset,
        )

    async def create_course(
        self,
        organization_id: int,
        data: CourseCreate,
        *,
        request_id: str | None = None,
    ) -> CourseResponse:
        course = await self.course_repo.create(
            organization_id=organization_id,
            title=data.title,
            description=data.description,
            duration_minutes=data.duration_minutes,
            is_published=data.is_published,
            thumbnail_url=data.thumbnail_url,
        )

        for module in data.modules:
            await self.course_repo.add_module(
                course_id=course.id,
                title=module.title,
                content=module.content,
                sort_order=module.sort_order,
                duration_minutes=module.duration_minutes,
            )

        course_with_modules = await self.course_repo.get_with_modules(course.id, organization_id)
        if course_with_modules is None:
            raise NotFoundError("Курс", course.id)
        await log_audit(
            self.session,
            action="course_created",
            entity_type="course",
            entity_id=str(course.id),
            organization_id=organization_id,
            user_id=None,
            request_id=request_id,
            details={"modules": len(data.modules)},
        )
        return CourseResponse.model_validate(course_with_modules)

    async def update_course(
        self,
        course_id: int,
        organization_id: int,
        data: CourseUpdate,
        *,
        request_id: str | None = None,
    ) -> CourseResponse:
        course = await self.course_repo.get_by_id(course_id)
        if course is None or course.organization_id != organization_id:
            raise NotFoundError("Курс", course_id)

        update_data = data.model_dump(exclude_unset=True, exclude={"modules"})
        updated = await self.course_repo.update(course_id, **update_data)
        if updated is None:
            raise NotFoundError("Курс", course_id)

        if data.modules is not None:
            # Удаляем старые модули и создаём заново (MVP-упрощение)
            updated.modules.clear()
            await self.session.flush()
            for module in data.modules:
                await self.course_repo.add_module(
                    course_id=course_id,
                    title=module.title,
                    content=module.content,
                    sort_order=module.sort_order,
                    duration_minutes=module.duration_minutes,
                )

        course_with_modules = await self.course_repo.get_with_modules(course_id, organization_id)
        if course_with_modules is None:
            raise NotFoundError("Курс", course_id)
        await log_audit(
            self.session,
            action="course_updated",
            entity_type="course",
            entity_id=str(course_id),
            organization_id=organization_id,
            user_id=None,
            request_id=request_id,
        )
        return CourseResponse.model_validate(course_with_modules)

    async def publish_course(
        self,
        course_id: int,
        organization_id: int,
        *,
        request_id: str | None = None,
    ) -> CourseResponse:
        course = await self.course_repo.get_by_id(course_id)
        if course is None or course.organization_id != organization_id:
            raise NotFoundError("Курс", course_id)

        updated = await self.course_repo.update(course_id, is_published=True)
        if updated is None:
            raise NotFoundError("Курс", course_id)
        course_with_modules = await self.course_repo.get_with_modules(updated.id, organization_id)
        if course_with_modules is None:
            raise NotFoundError("Курс", updated.id)
        await log_audit(
            self.session,
            action="course_published",
            entity_type="course",
            entity_id=str(course_id),
            organization_id=organization_id,
            user_id=None,
            request_id=request_id,
        )
        return CourseResponse.model_validate(course_with_modules)

    async def assign_course(
        self,
        course_id: int,
        organization_id: int,
        user_ids: list[UUID],
        *,
        actor_id: UUID | None = None,
        request_id: str | None = None,
    ) -> list[CourseAssignmentResponse]:
        course = await self.course_repo.get_by_id(course_id)
        if course is None or course.organization_id != organization_id or not course.is_published:
            raise NotFoundError("Курс", course_id)

        assignments: list[CourseAssignmentResponse] = []
        for user_id in user_ids:
            existing = await self.assignment_repo.get_for_user(
                course_id=course_id,
                user_id=user_id,
                organization_id=organization_id,
            )
            if existing:
                assignments.append(CourseAssignmentResponse.model_validate(existing))
                continue

            assignment = await self.assignment_repo.assign_course(
                course_id=course_id,
                organization_id=organization_id,
                user_id=user_id,
                due_at=None,
            )
            assignments.append(CourseAssignmentResponse.model_validate(assignment))
        await log_audit(
            self.session,
            action="course_assigned",
            entity_type="course",
            entity_id=str(course_id),
            organization_id=organization_id,
            user_id=str(actor_id) if actor_id else None,
            request_id=request_id,
            details={"assigned_count": len(assignments)},
        )
        return assignments

    async def update_progress(
        self,
        course_id: int,
        organization_id: int,
        user_id: UUID,
        progress_percent: int,
        *,
        request_id: str | None = None,
    ) -> CourseAssignmentResponse:
        assignment = await self.assignment_repo.get_for_user(course_id, user_id, organization_id)
        if assignment is None:
            raise NotFoundError("Назначение курса", course_id)

        status = assignment.status
        if progress_percent >= 100:
            status = AssignmentStatus.COMPLETED
            progress_percent = 100
        elif progress_percent > 0:
            status = AssignmentStatus.IN_PROGRESS

        updated = await self.assignment_repo.update_progress(
            assignment,
            progress_percent=progress_percent,
            status=status,
        )
        await log_audit(
            self.session,
            action="course_progress_updated",
            entity_type="course_assignment",
            entity_id=str(assignment.id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
            details={"progress_percent": progress_percent, "status": status.value},
        )
        return CourseAssignmentResponse.model_validate(updated)

    async def list_assignments_for_user(
        self,
        user_id: UUID,
        organization_id: int,
    ) -> list[CourseAssignmentResponse]:
        assignments = await self.assignment_repo.list_for_user(user_id, organization_id)
        return [CourseAssignmentResponse.model_validate(a) for a in assignments]
