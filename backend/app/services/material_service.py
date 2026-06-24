"""Сервис для работы с материалами базы знаний."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.db.repositories import CategoryRepository, MaterialRepository
from app.models import Category
from app.models.material import MaterialStatus, MaterialType, MaterialVisibility
from app.models.notification import Notification
from app.schemas.material import (
    ArticleCreate,
    CategoryCreate,
    MaterialCreate,
    MaterialListItem,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.services.utils import log_audit, utcnow


class MaterialService:
    """Сервис для работы с материалами базы знаний."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = MaterialRepository(session)
        self.category_repo = CategoryRepository(session)

    def _make_slug(self, name: str, slug: str | None) -> str:
        """Упрощённая нормализация slug."""
        base = slug or name
        return base.strip().lower().replace(" ", "-")

    async def create_material(
        self,
        *,
        organization_id: int,
        author_id: UUID,
        data: MaterialCreate,
        request_id: str | None = None,
    ) -> MaterialResponse:
        material = await self.repository.create(
            organization_id=organization_id,
            author_id=author_id,
            title=data.title,
            content=data.content,
            summary=data.summary,
            type=data.type,
            status=data.status,
            visibility=data.visibility,
            category_id=data.category_id,
            published_at=utcnow() if data.status == MaterialStatus.PUBLISHED else None,
        )
        await log_audit(
            self.session,
            action="material_created",
            entity_type="material",
            entity_id=str(material.id),
            organization_id=organization_id,
            user_id=str(author_id),
            request_id=request_id,
            details={"status": material.status},
        )
        return MaterialResponse.model_validate(material)

    async def create_article(
        self,
        *,
        organization_id: int,
        author_id: UUID,
        data: ArticleCreate,
        request_id: str | None = None,
    ) -> MaterialResponse:
        """Создать статью (тип фиксирован ARTICLE).

        Per-type точка входа: позже рядом появятся create_npa и т.д.
        Переиспользует общий репозиторий/аудит, тело хранится в базовой таблице.
        """
        material = await self.repository.create(
            organization_id=organization_id,
            author_id=author_id,
            title=data.title,
            content=data.content,
            content_format=data.content_format,
            summary=data.summary,
            type=MaterialType.ARTICLE,
            status=data.status,
            visibility=data.visibility,
            category_id=data.category_id,
            published_at=utcnow() if data.status == MaterialStatus.PUBLISHED else None,
        )
        await log_audit(
            self.session,
            action="article_created",
            entity_type="material",
            entity_id=str(material.id),
            organization_id=organization_id,
            user_id=str(author_id),
            request_id=request_id,
            details={"status": material.status, "type": MaterialType.ARTICLE},
        )
        return MaterialResponse.model_validate(material)

    async def update_material(
        self,
        material_id: UUID,
        *,
        organization_id: int,
        editor_id: UUID,
        data: MaterialUpdate,
        is_superuser: bool = False,
        request_id: str | None = None,
    ) -> MaterialResponse:
        material = await self.repository.get_by_id(material_id)
        if material is None or material.organization_id != organization_id:
            raise NotFoundError("Материал", str(material_id))
        if material.author_id != editor_id and not is_superuser:
            raise AuthorizationError("Редактировать материал может только его автор")

        update_data = data.model_dump(exclude_unset=True)
        # Оставляем только реально изменившиеся поля. Если изменений нет — не пишем,
        # чтобы не двигать дату изменения и автора правки на пустом сохранении.
        changed = {key: value for key, value in update_data.items() if getattr(material, key) != value}
        if not changed:
            return MaterialResponse.model_validate(material)

        if changed.get("status") == MaterialStatus.PUBLISHED:
            changed["published_at"] = material.published_at or utcnow()
        changed["updated_by_id"] = editor_id

        updated = await self.repository.update(material_id, **changed)
        await log_audit(
            self.session,
            action="material_updated",
            entity_type="material",
            entity_id=str(material_id),
            organization_id=organization_id,
            user_id=str(editor_id),
            request_id=request_id,
            details={"status": update_data.get("status", material.status)},
        )
        return MaterialResponse.model_validate(updated)

    async def publish(
        self,
        material_id: UUID,
        *,
        organization_id: int,
        editor_id: UUID,
        request_id: str | None = None,
    ) -> MaterialResponse:
        material = await self.repository.get_by_id(material_id)
        if material is None or material.organization_id != organization_id:
            raise NotFoundError("Материал", str(material_id))

        updated = await self.repository.update(
            material_id,
            status=MaterialStatus.PUBLISHED,
            published_at=utcnow(),
            updated_by_id=editor_id,
        )
        await log_audit(
            self.session,
            action="material_published",
            entity_type="material",
            entity_id=str(material_id),
            organization_id=organization_id,
            user_id=str(editor_id),
            request_id=request_id,
            details={"status": MaterialStatus.PUBLISHED},
        )
        return MaterialResponse.model_validate(updated)

    async def archive_material(
        self,
        material_id: UUID,
        *,
        organization_id: int,
        user_id: UUID,
        is_superuser: bool = False,
        request_id: str | None = None,
    ) -> MaterialResponse:
        """Перевести материал в архив (виден только автору, скрыт из общих списков)."""
        material = await self.repository.get_by_id(material_id)
        if material is None or material.organization_id != organization_id:
            raise NotFoundError("Материал", str(material_id))
        if material.author_id != user_id and not is_superuser:
            raise AuthorizationError("Архивировать материал может только его автор")

        updated = await self.repository.update(
            material_id,
            status=MaterialStatus.ARCHIVED,
            updated_by_id=user_id,
        )
        await log_audit(
            self.session,
            action="material_archived",
            entity_type="material",
            entity_id=str(material_id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
            details={"status": MaterialStatus.ARCHIVED},
        )
        return MaterialResponse.model_validate(updated)

    async def restore_material(
        self,
        material_id: UUID,
        *,
        organization_id: int,
        user_id: UUID,
        is_superuser: bool = False,
        request_id: str | None = None,
    ) -> MaterialResponse:
        """Восстановить материал из архива в черновик (только автор)."""
        material = await self.repository.get_by_id(material_id)
        if material is None or material.organization_id != organization_id:
            raise NotFoundError("Материал", str(material_id))
        if material.author_id != user_id and not is_superuser:
            raise AuthorizationError("Восстанавливать материал может только его автор")

        # Возврат в черновик: снимаем дату публикации, материал снова скрыт от всех.
        updated = await self.repository.update(
            material_id,
            status=MaterialStatus.DRAFT,
            published_at=None,
            updated_by_id=user_id,
        )
        await log_audit(
            self.session,
            action="material_restored",
            entity_type="material",
            entity_id=str(material_id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
            details={"status": MaterialStatus.DRAFT},
        )
        return MaterialResponse.model_validate(updated)

    async def delete_material(
        self,
        material_id: UUID,
        *,
        organization_id: int,
        user_id: UUID,
        is_superuser: bool = False,
        request_id: str | None = None,
    ) -> None:
        """Полностью удалить материал (только автор). Чистит связанные уведомления."""
        material = await self.repository.get_by_id(material_id)
        if material is None or material.organization_id != organization_id:
            raise NotFoundError("Материал", str(material_id))
        if material.author_id != user_id and not is_superuser:
            raise AuthorizationError("Удалять материал может только его автор")

        # Убираем уведомления-ссылки на этот материал, чтобы не было битых переходов.
        await self.session.execute(
            delete(Notification).where(
                Notification.entity_type == "material",
                Notification.entity_id == material_id,
            )
        )
        await self.repository.delete(material_id)
        await log_audit(
            self.session,
            action="material_deleted",
            entity_type="material",
            entity_id=str(material_id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
        )

    async def get_material(
        self,
        material_id: UUID,
        *,
        organization_id: int,
        requester_id: UUID | None = None,
        is_superuser: bool = False,
    ) -> MaterialResponse:
        material = await self.repository.get_with_relations(material_id)
        if material is None:
            raise NotFoundError("Материал", str(material_id))

        # Контроль доступа:
        # - опубликованное видно своей организации, а публичное — всем;
        # - черновик/архив видит только автор (или суперпользователь).
        if material.status == MaterialStatus.PUBLISHED:
            if material.organization_id != organization_id and material.visibility != MaterialVisibility.PUBLIC:
                raise NotFoundError("Материал", str(material_id))
        elif not (is_superuser or material.author_id == requester_id):
            raise NotFoundError("Материал", str(material_id))

        # Сериализуем ДО инкремента: increment_views делает flush и обновляет объект,
        # после чего ленивое чтение атрибутов в async-контексте падает (MissingGreenlet).
        # Автор и организация подгружены заранее (selectinload) — обращение безопасно.
        response = MaterialResponse.model_validate(material)
        response.author_name = material.author.name if material.author else None
        response.organization_name = material.organization.name if material.organization else None
        response.updated_by_name = material.updated_by.name if material.updated_by else None

        # Члены организации видят и черновики своей организации (чтение перед публикацией).
        # Счётчик просмотров увеличиваем только для опубликованных — чтобы не накручивать
        # его на предпросмотре автором.
        if material.status == MaterialStatus.PUBLISHED:
            await self.repository.increment_views(material_id)
        return response

    async def get_materials(
        self,
        *,
        organization_id: int,
        material_type: MaterialType | None = None,
        category_id: int | None = None,
        status: MaterialStatus | None = None,
        requester_id: UUID | None = None,
        is_superuser: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> MaterialListResponse:
        offset = (page - 1) * page_size

        if status is None or status == MaterialStatus.PUBLISHED:
            # Публичный список опубликованных (своя организация + публичные из других).
            materials, total = await self.repository.get_published(
                organization_id=organization_id,
                material_type=material_type,
                category_id=category_id,
                limit=page_size,
                offset=offset,
            )
        else:
            # Черновики/архив: строго внутри организации. Обычный пользователь видит
            # только свои, суперпользователь — всех авторов организации.
            materials, total = await self.repository.list_by_status(
                organization_id=organization_id,
                status=status,
                material_type=material_type,
                category_id=category_id,
                author_id=None if is_superuser else requester_id,
                limit=page_size,
                offset=offset,
            )

        items = [MaterialListItem.model_validate(m) for m in materials]
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return MaterialListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def list_categories(self, organization_id: int) -> list[Category]:
        """Список категорий организации."""
        return await self.category_repo.list_by_organization(organization_id)

    async def create_category(
        self, organization_id: int, data: CategoryCreate, request_id: str | None = None
    ) -> Category:
        """Создать категорию материалов."""
        slug = self._make_slug(data.name, data.slug)
        existing = await self.category_repo.get_by_slug(organization_id, slug)
        if existing:
            raise ConflictError("Категория с таким slug уже существует", field="slug")

        category = await self.category_repo.create(
            organization_id=organization_id,
            name=data.name,
            slug=slug,
            parent_id=data.parent_id,
            description=data.description,
            sort_order=data.sort_order,
        )
        await log_audit(
            self.session,
            action="category_created",
            entity_type="category",
            entity_id=str(category.id),
            organization_id=organization_id,
            user_id=None,
            request_id=request_id,
        )
        return category

    async def search(self, request: SearchRequest, *, organization_id: int) -> SearchResponse:
        offset = (request.page - 1) * request.page_size

        materials, total = await self.repository.search(
            request.query,
            organization_id=organization_id,
            material_type=request.type,
            category_id=request.category_id,
            limit=request.page_size,
            offset=offset,
        )

        items = [
            SearchResult(
                id=m.id,
                organization_id=m.organization_id,
                title=m.title,
                summary=m.summary,
                type=m.type,
                status=m.status,
                visibility=m.visibility,
                views_count=m.views_count,
                published_at=m.published_at,
                highlights=None,
            )
            for m in materials
        ]

        pages = (total + request.page_size - 1) // request.page_size if request.page_size > 0 else 0

        return SearchResponse(
            items=items,
            total=total,
            query=request.query,
            page=request.page,
            page_size=request.page_size,
            pages=pages,
        )

    async def get_popular(
        self,
        *,
        organization_id: int,
        material_type: MaterialType | None = None,
        limit: int = 10,
    ) -> list[MaterialListItem]:
        materials = await self.repository.get_popular(
            organization_id=organization_id,
            material_type=material_type,
            limit=limit,
        )
        return [MaterialListItem.model_validate(m) for m in materials]
