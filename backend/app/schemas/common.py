"""Общие схемы: пагинация, ответы и т.д."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Параметры пагинации для запросов списков."""

    page: int = Field(default=1, ge=1, description="Номер страницы")
    page_size: int = Field(default=20, ge=1, le=100, description="Размер страницы")

    @property
    def offset(self) -> int:
        """Вычислить смещение для SQL-запроса."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Вернуть лимит для SQL-запроса."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Ответ с пагинацией для списков."""

    items: list[T]
    total: int = Field(description="Общее количество элементов")
    page: int = Field(description="Текущая страница")
    page_size: int = Field(description="Размер страницы")
    pages: int = Field(description="Общее количество страниц")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Создать ответ с пагинацией.

        Args:
            items: Элементы текущей страницы.
            total: Общее количество элементов.
            page: Номер текущей страницы.
            page_size: Размер страницы.

        Returns:
            PaginatedResponse с вычисленным количеством страниц.
        """
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class ErrorDetail(BaseModel):
    """Детали ошибки."""

    code: str = Field(description="Код ошибки")
    message: str = Field(description="Сообщение об ошибке")
    details: dict = Field(default_factory=dict, description="Дополнительные детали")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой."""

    error: ErrorDetail
