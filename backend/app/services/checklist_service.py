"""Сервис подмодуля «Чек-листы»."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.db.repositories import ChecklistRepository, MaterialRepository
from app.models.checklist import Checklist, ChecklistItem, ChecklistStatus
from app.schemas.checklist import (
    ChecklistCreate,
    ChecklistItemInput,
    ChecklistItemResponse,
    ChecklistListItem,
    ChecklistListResponse,
    ChecklistResponse,
    ChecklistUpdate,
)
from app.services.utils import log_audit


class ChecklistService:
    """Сервис чек-листов (шаблонов)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ChecklistRepository(session)
        self.material_repo = MaterialRepository(session)

    async def _validate_references(self, items: list[ChecklistItemInput], *, organization_id: int) -> None:
        """Ссылки пунктов должны вести на материалы своей организации."""
        for item in items:
            if item.reference_material_id is None:
                continue
            material = await self.material_repo.get_by_id(item.reference_material_id)
            if material is None or material.organization_id != organization_id:
                raise ValidationError("Ссылка на материал недоступна или из другой организации")

    @staticmethod
    def _build_items(items: list[ChecklistItemInput]) -> list[ChecklistItem]:
        return [
            ChecklistItem(
                sort_order=index,
                text=item.text,
                answer_type=item.answer_type,
                required=item.required,
                help_text=item.help_text,
                reference_material_id=item.reference_material_id,
                reference_note=item.reference_note,
            )
            for index, item in enumerate(items)
        ]

    @staticmethod
    def _to_response(checklist: Checklist) -> ChecklistResponse:
        response = ChecklistResponse.model_validate(checklist)
        response.author_name = checklist.author.name if checklist.author else None
        response.updated_by_name = checklist.updated_by.name if checklist.updated_by else None
        items: list[ChecklistItemResponse] = []
        for item in checklist.items:
            item_response = ChecklistItemResponse.model_validate(item)
            item_response.reference_material_title = item.reference_material.title if item.reference_material else None
            items.append(item_response)
        response.items = items
        return response

    async def list_checklists(
        self,
        *,
        organization_id: int,
        is_owner: bool,
        status: ChecklistStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ChecklistListResponse:
        # Владелец видит все статусы (или фильтр), обычный пользователь — только опубликованные.
        if not is_owner:
            statuses = [ChecklistStatus.PUBLISHED]
        elif status is not None:
            statuses = [status]
        else:
            statuses = list(ChecklistStatus)

        offset = (page - 1) * page_size
        checklists, total = await self.repository.list_for_org(
            organization_id=organization_id,
            statuses=statuses,
            limit=page_size,
            offset=offset,
        )
        items = []
        for checklist in checklists:
            list_item = ChecklistListItem.model_validate(checklist)
            list_item.item_count = len(checklist.items)
            items.append(list_item)
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return ChecklistListResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)

    async def get_checklist(
        self,
        checklist_id: UUID,
        *,
        organization_id: int,
        is_owner: bool,
    ) -> ChecklistResponse:
        checklist = await self.repository.get_with_items(checklist_id)
        if checklist is None or checklist.organization_id != organization_id:
            raise NotFoundError("Чек-лист", str(checklist_id))
        # Черновики и архив видит только владелец организации.
        if checklist.status != ChecklistStatus.PUBLISHED and not is_owner:
            raise NotFoundError("Чек-лист", str(checklist_id))
        return self._to_response(checklist)

    async def create_checklist(
        self,
        *,
        organization_id: int,
        author_id: UUID,
        data: ChecklistCreate,
        request_id: str | None = None,
    ) -> ChecklistResponse:
        await self._validate_references(data.items, organization_id=organization_id)
        checklist = Checklist(
            organization_id=organization_id,
            author_id=author_id,
            title=data.title,
            description=data.description,
            status=data.status,
            items=self._build_items(data.items),
        )
        self.session.add(checklist)
        await self.session.flush()

        await log_audit(
            self.session,
            action="checklist_created",
            entity_type="checklist",
            entity_id=str(checklist.id),
            organization_id=organization_id,
            user_id=str(author_id),
            request_id=request_id,
            details={"status": checklist.status, "items": len(data.items)},
        )
        loaded = await self.repository.get_with_items(checklist.id)
        assert loaded is not None
        return self._to_response(loaded)

    async def update_checklist(
        self,
        checklist_id: UUID,
        *,
        organization_id: int,
        editor_id: UUID,
        data: ChecklistUpdate,
        request_id: str | None = None,
    ) -> ChecklistResponse:
        checklist = await self.repository.get_with_items(checklist_id)
        if checklist is None or checklist.organization_id != organization_id:
            raise NotFoundError("Чек-лист", str(checklist_id))

        if data.title is not None:
            checklist.title = data.title
        if data.description is not None:
            checklist.description = data.description
        if data.status is not None:
            checklist.status = data.status
        if data.items is not None:
            await self._validate_references(data.items, organization_id=organization_id)
            checklist.items = self._build_items(data.items)
        checklist.updated_by_id = editor_id
        await self.session.flush()

        await log_audit(
            self.session,
            action="checklist_updated",
            entity_type="checklist",
            entity_id=str(checklist_id),
            organization_id=organization_id,
            user_id=str(editor_id),
            request_id=request_id,
            details={"status": checklist.status},
        )
        loaded = await self.repository.get_with_items(checklist_id)
        assert loaded is not None
        return self._to_response(loaded)

    async def _set_status(
        self,
        checklist_id: UUID,
        *,
        organization_id: int,
        editor_id: UUID,
        status: ChecklistStatus,
        action: str,
        request_id: str | None,
    ) -> ChecklistResponse:
        checklist = await self.repository.get_with_items(checklist_id)
        if checklist is None or checklist.organization_id != organization_id:
            raise NotFoundError("Чек-лист", str(checklist_id))
        checklist.status = status
        checklist.updated_by_id = editor_id
        await self.session.flush()
        await log_audit(
            self.session,
            action=action,
            entity_type="checklist",
            entity_id=str(checklist_id),
            organization_id=organization_id,
            user_id=str(editor_id),
            request_id=request_id,
            details={"status": status},
        )
        loaded = await self.repository.get_with_items(checklist_id)
        assert loaded is not None
        return self._to_response(loaded)

    async def publish_checklist(
        self, checklist_id: UUID, *, organization_id: int, editor_id: UUID, request_id: str | None = None
    ) -> ChecklistResponse:
        return await self._set_status(
            checklist_id,
            organization_id=organization_id,
            editor_id=editor_id,
            status=ChecklistStatus.PUBLISHED,
            action="checklist_published",
            request_id=request_id,
        )

    async def archive_checklist(
        self, checklist_id: UUID, *, organization_id: int, editor_id: UUID, request_id: str | None = None
    ) -> ChecklistResponse:
        return await self._set_status(
            checklist_id,
            organization_id=organization_id,
            editor_id=editor_id,
            status=ChecklistStatus.ARCHIVED,
            action="checklist_archived",
            request_id=request_id,
        )

    async def delete_checklist(
        self, checklist_id: UUID, *, organization_id: int, user_id: UUID, request_id: str | None = None
    ) -> None:
        checklist = await self.repository.get_by_id(checklist_id)
        if checklist is None or checklist.organization_id != organization_id:
            raise NotFoundError("Чек-лист", str(checklist_id))
        await self.repository.delete(checklist_id)
        await log_audit(
            self.session,
            action="checklist_deleted",
            entity_type="checklist",
            entity_id=str(checklist_id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
        )
