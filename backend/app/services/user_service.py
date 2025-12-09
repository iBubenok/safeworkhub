"""Сервис для работы с пользователями."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EmailAlreadyExistsError, UserNotFoundError
from app.core.security import get_password_hash
from app.db.repositories import UserRepository
from app.models import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """Сервис для работы с пользователями.

    Инкапсулирует бизнес-логику работы с пользователями.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def get_user(self, user_id: UUID) -> UserResponse:
        """Получить пользователя по ID.

        Args:
            user_id: ID пользователя.

        Returns:
            Данные пользователя.

        Raises:
            UserNotFoundError: Пользователь не найден.
        """
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        return UserResponse.model_validate(user)

    async def get_user_by_email(self, email: str) -> UserResponse:
        """Получить пользователя по email.

        Args:
            email: Email пользователя.

        Returns:
            Данные пользователя.

        Raises:
            UserNotFoundError: Пользователь не найден.
        """
        user = await self.repository.get_by_email(email)
        if user is None:
            raise UserNotFoundError()
        return UserResponse.model_validate(user)

    async def create_user(
        self,
        data: UserCreate,
        organization_id: int | None = None,
    ) -> UserResponse:
        """Создать нового пользователя.

        Args:
            data: Данные для создания пользователя.
            organization_id: ID организации для привязки.

        Returns:
            Созданный пользователь.

        Raises:
            EmailAlreadyExistsError: Email уже занят.
        """
        if await self.repository.is_email_taken(data.email):
            raise EmailAlreadyExistsError(data.email)

        user = await self.repository.create(
            email=data.email.lower(),
            password_hash=get_password_hash(data.password),
            name=data.name,
        )

        return UserResponse.model_validate(user)

    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
    ) -> UserResponse:
        """Обновить данные пользователя.

        Args:
            user_id: ID пользователя.
            data: Данные для обновления.

        Returns:
            Обновлённый пользователь.

        Raises:
            UserNotFoundError: Пользователь не найден.
            EmailAlreadyExistsError: Новый email уже занят.
        """
        # Проверка существования
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        # Проверка уникальности email, если он меняется
        if data.email and data.email.lower() != user.email:
            if await self.repository.is_email_taken(data.email, exclude_user_id=user_id):
                raise EmailAlreadyExistsError(data.email)

        # Обновление
        update_data = data.model_dump(exclude_unset=True)
        if "email" in update_data:
            update_data["email"] = update_data["email"].lower()

        updated_user = await self.repository.update(user_id, **update_data)
        return UserResponse.model_validate(updated_user)

    async def deactivate_user(self, user_id: UUID) -> UserResponse:
        """Деактивировать пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            Деактивированный пользователь.

        Raises:
            UserNotFoundError: Пользователь не найден.
        """
        user = await self.repository.update(user_id, is_active=False)
        if user is None:
            raise UserNotFoundError(str(user_id))
        return UserResponse.model_validate(user)

    async def search_users(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[UserResponse]:
        """Поиск пользователей.

        Args:
            query: Поисковый запрос.
            limit: Максимальное количество результатов.
            offset: Смещение.

        Returns:
            Список найденных пользователей.
        """
        users = await self.repository.search(query, limit=limit, offset=offset)
        return [UserResponse.model_validate(u) for u in users]
