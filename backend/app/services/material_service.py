"""Сервис для работы с материалами базы знаний."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.db.repositories import CategoryRepository, MaterialRepository
from app.models import Category, Material, MaterialAttachment
from app.models.material import MaterialStatus, MaterialType, MaterialVisibility
from app.models.material_version import MaterialVersion
from app.models.news import News
from app.models.notification import Notification
from app.models.npa import Npa
from app.schemas.material import (
    ArticleCreate,
    AttachmentResponse,
    CategoryCreate,
    MaterialCreate,
    MaterialListItem,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
    MaterialVersionResponse,
    NewsCreate,
    NewsDetail,
    NpaCreate,
    NpaDetail,
    SearchRequest,
    SearchResponse,
    SearchResult,
    TemplateCreate,
)
from app.services.file_storage import LocalFileStorage, StorageLimitExceeded
from app.services.utils import log_audit, utcnow


class MaterialService:
    """Сервис для работы с материалами базы знаний."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = MaterialRepository(session)
        self.category_repo = CategoryRepository(session)
        self.storage = LocalFileStorage(settings.storage_local_path)

    def _make_slug(self, name: str, slug: str | None) -> str:
        """Упрощённая нормализация slug."""
        base = slug or name
        return base.strip().lower().replace(" ", "-")

    # Поля, попадающие в снимок версии. Добавление нового редактируемого поля —
    # только сюда (таблица версий менять не нужно, снимок в JSON).
    _VERSIONED_FIELDS = ("title", "summary", "content", "content_format")

    @classmethod
    def _snapshot(cls, material: Material) -> dict[str, object]:
        """Снимок версионируемых полей материала."""
        return {field: getattr(material, field) for field in cls._VERSIONED_FIELDS}

    async def _add_version(self, material: Material, *, editor_id: UUID, change_note: str | None) -> None:
        """Создать новую версию-снимок материала."""
        version = MaterialVersion(
            material_id=material.id,
            version_no=await self.repository.next_version_no(material.id),
            editor_id=editor_id,
            change_note=change_note,
            snapshot=self._snapshot(material),
        )
        self.session.add(version)
        await self.session.flush()

    @staticmethod
    def _to_list_item(material: Material) -> MaterialListItem:
        """Краткая карточка материала с названием организации-автора.

        organization подгружается заранее (joinedload), поэтому обращение к
        material.organization безопасно в async-контексте.
        """
        item = MaterialListItem.model_validate(material)
        item.organization_name = material.organization.name if material.organization else None
        item.attachment_count = len(material.attachments)
        return item

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
        await self._add_version(material, editor_id=author_id, change_note=None)
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
        await self._add_version(material, editor_id=author_id, change_note=None)
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

    async def create_news(
        self,
        *,
        organization_id: int,
        author_id: UUID,
        data: NewsCreate,
        request_id: str | None = None,
    ) -> MaterialResponse:
        """Создать новость: базовый материал (type=NEWS) + деталь-строку news."""
        material = await self.repository.create(
            organization_id=organization_id,
            author_id=author_id,
            title=data.title,
            content=data.content,
            content_format=data.content_format,
            summary=data.summary,
            type=MaterialType.NEWS,
            status=data.status,
            visibility=data.visibility,
            category_id=data.category_id,
            published_at=utcnow() if data.status == MaterialStatus.PUBLISHED else None,
        )
        detail = News(
            material_id=material.id,
            source_url=data.source_url,
            event_date=data.event_date,
            cover_image_url=data.cover_image_url,
            tags=data.tags,
        )
        self.session.add(detail)
        await self.session.flush()

        await self._add_version(material, editor_id=author_id, change_note=None)
        await log_audit(
            self.session,
            action="news_created",
            entity_type="material",
            entity_id=str(material.id),
            organization_id=organization_id,
            user_id=str(author_id),
            request_id=request_id,
            details={"status": material.status, "type": MaterialType.NEWS},
        )
        response = MaterialResponse.model_validate(material)
        response.news = NewsDetail.model_validate(detail)
        return response

    async def create_npa(
        self,
        *,
        organization_id: int,
        author_id: UUID,
        data: NpaCreate,
        request_id: str | None = None,
    ) -> MaterialResponse:
        """Создать НПА: базовый материал (type=NPA) + деталь-строку npa."""
        material = await self.repository.create(
            organization_id=organization_id,
            author_id=author_id,
            title=data.title,
            content=data.content,
            content_format=data.content_format,
            summary=data.summary,
            type=MaterialType.NPA,
            status=data.status,
            visibility=data.visibility,
            category_id=data.category_id,
            published_at=utcnow() if data.status == MaterialStatus.PUBLISHED else None,
        )
        detail = Npa(
            material_id=material.id,
            act_kind=data.act_kind,
            level=data.level,
            act_status=data.act_status,
            document_number=data.document_number,
            adoption_date=data.adoption_date,
            effective_date=data.effective_date,
            revision_date=data.revision_date,
            issuing_authority=data.issuing_authority,
            region=data.region,
            official_source_url=data.official_source_url,
        )
        self.session.add(detail)
        await self.session.flush()

        await self._add_version(material, editor_id=author_id, change_note=None)
        await log_audit(
            self.session,
            action="npa_created",
            entity_type="material",
            entity_id=str(material.id),
            organization_id=organization_id,
            user_id=str(author_id),
            request_id=request_id,
            details={"status": material.status, "type": MaterialType.NPA},
        )
        response = MaterialResponse.model_validate(material)
        response.npa = NpaDetail.model_validate(detail)
        return response

    async def create_template(
        self,
        *,
        organization_id: int,
        author_id: UUID,
        data: TemplateCreate,
        request_id: str | None = None,
    ) -> MaterialResponse:
        """Создать шаблон (тип фиксирован TEMPLATE). Файлы грузятся отдельно."""
        material = await self.repository.create(
            organization_id=organization_id,
            author_id=author_id,
            title=data.title,
            content=data.content,
            content_format=data.content_format,
            summary=data.summary,
            type=MaterialType.TEMPLATE,
            status=data.status,
            visibility=data.visibility,
            category_id=data.category_id,
            published_at=utcnow() if data.status == MaterialStatus.PUBLISHED else None,
        )
        await self._add_version(material, editor_id=author_id, change_note=None)
        await log_audit(
            self.session,
            action="template_created",
            entity_type="material",
            entity_id=str(material.id),
            organization_id=organization_id,
            user_id=str(author_id),
            request_id=request_id,
            details={"status": material.status, "type": MaterialType.TEMPLATE},
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
        # change_note — поле версии, не материала: убираем до диффа.
        change_note = update_data.pop("change_note", None)
        # Оставляем только реально изменившиеся поля. Если изменений нет — не пишем,
        # чтобы не двигать дату изменения и автора правки на пустом сохранении.
        changed = {key: value for key, value in update_data.items() if getattr(material, key) != value}
        if not changed:
            return MaterialResponse.model_validate(material)

        if changed.get("status") == MaterialStatus.PUBLISHED:
            changed["published_at"] = material.published_at or utcnow()
        changed["updated_by_id"] = editor_id

        updated = await self.repository.update(material_id, **changed)
        # Новую версию создаём только при изменении версионируемого поля
        # (правка контента), а не при смене статуса/видимости.
        if updated is not None and any(field in changed for field in self._VERSIONED_FIELDS):
            await self._add_version(updated, editor_id=editor_id, change_note=change_note)
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
        """Полностью удалить материал (только автор). Чистит уведомления и файлы."""
        material = await self.repository.get_with_relations(material_id)
        if material is None or material.organization_id != organization_id:
            raise NotFoundError("Материал", str(material_id))
        if material.author_id != user_id and not is_superuser:
            raise AuthorizationError("Удалять материал может только его автор")

        # Запоминаем ключи файлов до удаления строки (каскад уберёт строки вложений).
        storage_keys = [a.storage_key for a in material.attachments]

        # Убираем уведомления-ссылки на этот материал, чтобы не было битых переходов.
        await self.session.execute(
            delete(Notification).where(
                Notification.entity_type == "material",
                Notification.entity_id == material_id,
            )
        )
        await self.repository.delete(material_id)
        # Физические файлы удаляем после строки (best-effort; вне транзакции БД).
        for key in storage_keys:
            await self.storage.delete(key)
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
        # Деталь новости (joinedload в get_with_relations) — если это новость.
        response.news = NewsDetail.model_validate(material.news) if material.news else None
        # Деталь НПА (joinedload) — если это НПА.
        response.npa = NpaDetail.model_validate(material.npa) if material.npa else None
        # Прикреплённые файлы (selectinload) — для шаблонов и пр.
        response.attachments = [AttachmentResponse.model_validate(a) for a in material.attachments]

        # Члены организации видят и черновики своей организации (чтение перед публикацией).
        # Счётчик просмотров увеличиваем только для опубликованных — чтобы не накручивать
        # его на предпросмотре автором.
        if material.status == MaterialStatus.PUBLISHED:
            await self.repository.increment_views(material_id)
        return response

    @staticmethod
    def _ensure_visible(
        material: Material,
        *,
        organization_id: int,
        requester_id: UUID | None,
        is_superuser: bool,
    ) -> None:
        """Контроль доступа к материалу (как в get_material). Иначе 404."""
        if material.status == MaterialStatus.PUBLISHED:
            if material.organization_id != organization_id and material.visibility != MaterialVisibility.PUBLIC:
                raise NotFoundError("Материал", str(material.id))
        elif not (is_superuser or material.author_id == requester_id):
            raise NotFoundError("Материал", str(material.id))

    def _validate_upload(self, upload: UploadFile, current_count: int) -> str:
        """Проверить количество/имя/расширение. Вернуть расширение (без точки)."""
        if current_count >= settings.max_attachments_per_material:
            raise ValidationError(f"Достигнут лимит вложений ({settings.max_attachments_per_material})")
        filename = (upload.filename or "").strip()
        if not filename:
            raise ValidationError("У файла отсутствует имя")
        ext = Path(filename).suffix.lower().lstrip(".")
        allowed = {e.lower() for e in settings.allowed_upload_extensions}
        if ext not in allowed:
            raise ValidationError(f"Недопустимый тип файла .{ext}. Разрешены: {', '.join(sorted(allowed))}")
        return ext

    async def add_attachment(
        self,
        material_id: UUID,
        *,
        organization_id: int,
        user_id: UUID,
        is_superuser: bool,
        upload: UploadFile,
        request_id: str | None = None,
    ) -> AttachmentResponse:
        """Загрузить файл к материалу (только автор/суперпользователь)."""
        material = await self.repository.get_with_relations(material_id)
        if material is None or material.organization_id != organization_id:
            raise NotFoundError("Материал", str(material_id))
        if material.author_id != user_id and not is_superuser:
            raise AuthorizationError("Прикреплять файлы может только автор материала")

        ext = self._validate_upload(upload, len(material.attachments))
        key = f"attachments/{organization_id}/{uuid4().hex}.{ext}"
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        try:
            size = await self.storage.save(key, upload, max_bytes=max_bytes)
        except StorageLimitExceeded as exc:
            raise ValidationError(f"Файл превышает лимит {settings.max_upload_size_mb} МБ") from exc

        attachment = MaterialAttachment(
            material_id=material.id,
            filename=Path(upload.filename or "file").name[:255],
            storage_key=key,
            content_type=upload.content_type or "application/octet-stream",
            size_bytes=size,
            uploaded_by_id=user_id,
        )
        self.session.add(attachment)
        await self.session.flush()

        await log_audit(
            self.session,
            action="attachment_added",
            entity_type="material",
            entity_id=str(material.id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
            details={"attachment_id": str(attachment.id), "filename": attachment.filename},
        )
        return AttachmentResponse.model_validate(attachment)

    async def delete_attachment(
        self,
        material_id: UUID,
        attachment_id: UUID,
        *,
        organization_id: int,
        user_id: UUID,
        is_superuser: bool,
        request_id: str | None = None,
    ) -> None:
        """Удалить вложение материала (только автор/суперпользователь)."""
        material = await self.repository.get_by_id(material_id)
        if material is None or material.organization_id != organization_id:
            raise NotFoundError("Материал", str(material_id))
        if material.author_id != user_id and not is_superuser:
            raise AuthorizationError("Удалять файлы может только автор материала")

        attachment = await self.session.get(MaterialAttachment, attachment_id)
        if attachment is None or attachment.material_id != material_id:
            raise NotFoundError("Вложение", str(attachment_id))

        key = attachment.storage_key
        await self.session.delete(attachment)
        await self.session.flush()
        await self.storage.delete(key)

        await log_audit(
            self.session,
            action="attachment_deleted",
            entity_type="material",
            entity_id=str(material_id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
            details={"attachment_id": str(attachment_id)},
        )

    async def get_attachment_for_download(
        self,
        material_id: UUID,
        attachment_id: UUID,
        *,
        organization_id: int,
        requester_id: UUID,
        is_superuser: bool = False,
    ) -> tuple[MaterialAttachment, Iterator[bytes]]:
        """Вложение + поток файла с проверкой приватности материала."""
        material = await self.repository.get_by_id(material_id)
        if material is None:
            raise NotFoundError("Материал", str(material_id))
        self._ensure_visible(
            material,
            organization_id=organization_id,
            requester_id=requester_id,
            is_superuser=is_superuser,
        )
        attachment = await self.session.get(MaterialAttachment, attachment_id)
        if attachment is None or attachment.material_id != material_id:
            raise NotFoundError("Вложение", str(attachment_id))
        return attachment, self.storage.open_stream(attachment.storage_key)

    async def get_versions(
        self,
        material_id: UUID,
        *,
        organization_id: int,
        requester_id: UUID,
        is_superuser: bool = False,
    ) -> list[MaterialVersionResponse]:
        """История версий материала (с проверкой приватности материала)."""
        material = await self.repository.get_by_id(material_id)
        if material is None:
            raise NotFoundError("Материал", str(material_id))
        self._ensure_visible(
            material,
            organization_id=organization_id,
            requester_id=requester_id,
            is_superuser=is_superuser,
        )
        versions = await self.repository.list_versions(material_id)
        items: list[MaterialVersionResponse] = []
        for version in versions:
            item = MaterialVersionResponse.model_validate(version)
            item.editor_name = version.editor.name if version.editor else None
            items.append(item)
        return items

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

        items = [self._to_list_item(m) for m in materials]
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

    async def search(
        self,
        request: SearchRequest,
        *,
        organization_id: int,
        requester_id: UUID | None = None,
        is_superuser: bool = False,
    ) -> SearchResponse:
        offset = (request.page - 1) * request.page_size

        # По опубликованным — без фильтра автора; по черновикам/архиву обычный
        # пользователь ищет только свои, суперпользователь — всех авторов организации.
        published = request.status is None or request.status == MaterialStatus.PUBLISHED
        author_id = None if (is_superuser or published) else requester_id

        materials, total = await self.repository.search(
            request.query,
            organization_id=organization_id,
            status=request.status,
            material_type=request.type,
            category_id=request.category_id,
            author_id=author_id,
            limit=request.page_size,
            offset=offset,
        )

        items = [
            SearchResult(
                id=m.id,
                organization_id=m.organization_id,
                organization_name=m.organization.name if m.organization else None,
                title=m.title,
                summary=m.summary,
                type=m.type,
                status=m.status,
                visibility=m.visibility,
                views_count=m.views_count,
                published_at=m.published_at,
                attachment_count=len(m.attachments),
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
        return [self._to_list_item(m) for m in materials]
