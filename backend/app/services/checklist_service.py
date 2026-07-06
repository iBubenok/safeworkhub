"""Сервис подмодуля «Чек-листы»."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.db.repositories import ChecklistRepository, MaterialRepository
from app.models.checklist import (
    Checklist,
    ChecklistItem,
    ChecklistItemReference,
    ChecklistNodeType,
    ChecklistStatus,
    ChecklistVisibility,
)
from app.schemas.checklist import (
    ChecklistCreate,
    ChecklistListItem,
    ChecklistListResponse,
    ChecklistNodeInput,
    ChecklistNodeResponse,
    ChecklistReferenceResponse,
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

    async def _validate_references(self, nodes: list[ChecklistNodeInput], *, organization_id: int) -> None:
        """Ссылки пунктов (рекурсивно) должны вести на материалы своей организации."""
        for node in nodes:
            for ref in node.references:
                if ref.material_id is None:
                    continue
                material = await self.material_repo.get_by_id(ref.material_id)
                if material is None or material.organization_id != organization_id:
                    raise ValidationError("Ссылка на материал недоступна или из другой организации")
            await self._validate_references(node.children, organization_id=organization_id)

    def _insert_tree(
        self, checklist_id: UUID, nodes: list[ChecklistNodeInput], *, parent_id: UUID | None = None
    ) -> int:
        """Рекурсивно создать узлы дерева. Возвращает число узлов-пунктов (item)."""
        item_count = 0
        for index, node in enumerate(nodes):
            node_id = uuid4()
            is_item = node.node_type == ChecklistNodeType.ITEM
            self.session.add(
                ChecklistItem(
                    id=node_id,
                    checklist_id=checklist_id,
                    parent_id=parent_id,
                    node_type=node.node_type,
                    sort_order=index,
                    text=node.text,
                    answer_type=node.answer_type if is_item else None,
                    required=node.required,
                    help_text=node.help_text,
                )
            )
            if is_item:
                item_count += 1
                ref_order = 0
                for ref in node.references:
                    # Отбрасываем пустые ссылки (без материала и без заметки).
                    if ref.material_id is None and not (ref.note and ref.note.strip()):
                        continue
                    self.session.add(
                        ChecklistItemReference(
                            item_id=node_id,
                            sort_order=ref_order,
                            material_id=ref.material_id,
                            note=ref.note.strip() if ref.note else None,
                        )
                    )
                    ref_order += 1
            else:
                item_count += self._insert_tree(checklist_id, node.children, parent_id=node_id)
        return item_count

    @staticmethod
    def _build_tree(flat_items: list[ChecklistItem]) -> list[ChecklistNodeResponse]:
        """Собрать вложенное дерево ответов из плоского списка узлов."""
        children_by_parent: dict[UUID | None, list[ChecklistItem]] = {}
        for item in flat_items:
            children_by_parent.setdefault(item.parent_id, []).append(item)

        def build(parent_id: UUID | None) -> list[ChecklistNodeResponse]:
            nodes = sorted(children_by_parent.get(parent_id, []), key=lambda i: i.sort_order)
            result: list[ChecklistNodeResponse] = []
            for item in nodes:
                node = ChecklistNodeResponse.model_validate(item)
                node.references = [
                    ChecklistReferenceResponse(
                        id=ref.id,
                        material_id=ref.material_id,
                        material_title=ref.material.title if ref.material else None,
                        note=ref.note,
                    )
                    for ref in sorted(item.references, key=lambda r: r.sort_order)
                ]
                node.children = build(item.id)
                result.append(node)
            return result

        return build(None)

    def _to_response(self, checklist: Checklist) -> ChecklistResponse:
        response = ChecklistResponse.model_validate(checklist)
        response.organization_name = checklist.organization.name if checklist.organization else None
        response.author_name = checklist.author.name if checklist.author else None
        response.updated_by_name = checklist.updated_by.name if checklist.updated_by else None
        response.items = self._build_tree(list(checklist.items))
        return response

    async def list_checklists(
        self,
        *,
        organization_id: int,
        is_owner: bool,
        status: ChecklistStatus | None = None,
        search: str | None = None,
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
            search=search,
            limit=page_size,
            offset=offset,
        )
        items = []
        for checklist in checklists:
            # runs_count берётся из колонки (монотонный счётчик использований) автоматически.
            list_item = ChecklistListItem.model_validate(checklist)
            list_item.item_count = sum(1 for it in checklist.items if it.node_type == ChecklistNodeType.ITEM)
            list_item.organization_name = checklist.organization.name if checklist.organization else None
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
        if checklist is None:
            raise NotFoundError("Чек-лист", str(checklist_id))
        is_own = checklist.organization_id == organization_id
        if not is_own:
            # Чужой чек-лист доступен, только если он публичный и опубликован.
            if checklist.visibility != ChecklistVisibility.PUBLIC or checklist.status != ChecklistStatus.PUBLISHED:
                raise NotFoundError("Чек-лист", str(checklist_id))
        elif checklist.status != ChecklistStatus.PUBLISHED and not is_owner:
            # Свои черновики и архив видит только владелец организации.
            raise NotFoundError("Чек-лист", str(checklist_id))
        # Сериализуем до инкремента; считаем просмотры только у опубликованных.
        response = self._to_response(checklist)
        if checklist.status == ChecklistStatus.PUBLISHED:
            await self.repository.increment_views(checklist_id)
        return response

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
            visibility=data.visibility,
        )
        self.session.add(checklist)
        await self.session.flush()
        item_count = self._insert_tree(checklist.id, data.items)
        await self.session.flush()

        await log_audit(
            self.session,
            action="checklist_created",
            entity_type="checklist",
            entity_id=str(checklist.id),
            organization_id=organization_id,
            user_id=str(author_id),
            request_id=request_id,
            details={"status": checklist.status, "items": item_count},
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
        if data.visibility is not None:
            checklist.visibility = data.visibility
        if data.items is not None:
            await self._validate_references(data.items, organization_id=organization_id)
            # Заменяем всё дерево: удаляем старые узлы, вставляем новые.
            await self.session.execute(delete(ChecklistItem).where(ChecklistItem.checklist_id == checklist_id))
            await self.session.flush()
            self._insert_tree(checklist_id, data.items)
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
        # Коллекция items была загружена ранее; после Core-delete/insert сбрасываем кэш,
        # чтобы перечитать актуальное дерево.
        self.session.expire(checklist)
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
