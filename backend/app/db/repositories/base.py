"""Базовый репозиторий с CRUD-операциями."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Базовый репозиторий с типовыми CRUD-операциями.

    Предоставляет стандартные методы для работы с сущностями:
    создание, чтение, обновление, удаление.

    Attributes:
        model: Класс SQLAlchemy-модели.
        session: Асинхронная сессия БД.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        """Инициализация репозитория.

        Args:
            model: Класс SQLAlchemy-модели.
            session: Асинхронная сессия БД.
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID | int) -> ModelType | None:
        """Получить запись по ID.

        Args:
            id: Идентификатор записи.

        Returns:
            Найденная запись или None.
        """
        return await self.session.get(self.model, id)

    async def get_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelType]:
        """Получить все записи с пагинацией.

        Args:
            limit: Максимальное количество записей.
            offset: Смещение от начала.

        Returns:
            Список записей.
        """
        query = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Подсчитать общее количество записей.

        Returns:
            Количество записей.
        """
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelType:
        """Создать новую запись.

        Args:
            **kwargs: Атрибуты для создания записи.

        Returns:
            Созданная запись.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(
        self,
        id: UUID | int,
        **kwargs: Any,
    ) -> ModelType | None:
        """Обновить запись по ID.

        Args:
            id: Идентификатор записи.
            **kwargs: Атрибуты для обновления.

        Returns:
            Обновлённая запись или None, если не найдена.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID | int) -> bool:
        """Удалить запись по ID.

        Args:
            id: Идентификатор записи.

        Returns:
            True если запись удалена, False если не найдена.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def exists(self, id: UUID | int) -> bool:
        """Проверить существование записи.

        Args:
            id: Идентификатор записи.

        Returns:
            True если запись существует.
        """
        query = select(func.count()).select_from(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one() > 0
