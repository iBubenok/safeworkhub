"""Сервис аутентификации и регистрации."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    ConflictError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.db.repositories import UserRepository, OrganizationRepository
from app.models import Organization, OrganizationUser, Subscription, User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)


class AuthService:
    """Сервис аутентификации.

    Обрабатывает логин, регистрацию и управление токенами.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Аутентификация пользователя.

        Args:
            data: Данные для входа (email, пароль).

        Returns:
            TokenResponse с access и refresh токенами.

        Raises:
            InvalidCredentialsError: Неверный email или пароль.
        """
        user = await self.user_repo.get_by_email(data.email)

        if user is None or not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError()

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Обновление токенов по refresh token.

        Args:
            refresh_token: Текущий refresh token.

        Returns:
            TokenResponse с новыми токенами.

        Raises:
            InvalidCredentialsError: Невалидный refresh token.
        """
        user_id = verify_token(refresh_token, token_type="refresh")
        if user_id is None:
            raise InvalidCredentialsError()

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError()

        new_access_token = create_access_token(subject=str(user.id))
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def register(self, data: RegisterRequest) -> RegisterResponse:
        """Регистрация новой организации с администратором.

        Args:
            data: Данные для регистрации.

        Returns:
            RegisterResponse с ID созданных сущностей.

        Raises:
            EmailAlreadyExistsError: Email уже зарегистрирован.
            ConflictError: ИНН уже зарегистрирован.
        """
        # Проверка уникальности email
        if await self.user_repo.is_email_taken(data.admin_email):
            raise EmailAlreadyExistsError(data.admin_email)

        # Проверка уникальности ИНН
        if await self.org_repo.is_inn_taken(data.inn):
            raise ConflictError(
                message="Организация с таким ИНН уже зарегистрирована",
                field="inn",
            )

        # Создание организации
        organization = Organization(
            name=data.organization_name,
            inn=data.inn,
        )
        self.session.add(organization)
        await self.session.flush()

        # Создание пользователя-администратора
        user = User(
            email=data.admin_email.lower(),
            password_hash=get_password_hash(data.admin_password),
            name=data.admin_name,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()

        # Связь пользователя с организацией
        membership = OrganizationUser(
            organization_id=organization.id,
            user_id=user.id,
            role="admin",
            joined_at=datetime.now(timezone.utc),
        )
        self.session.add(membership)

        # Создание пробной подписки
        trial_end = datetime.now(timezone.utc) + timedelta(days=14)
        subscription = Subscription(
            organization_id=organization.id,
            tariff_id=1,  # Базовый тариф (должен существовать в БД)
            status="trial",
            trial_ends_at=trial_end,
            expires_at=trial_end,
        )
        self.session.add(subscription)

        await self.session.flush()

        return RegisterResponse(
            organization_id=organization.id,
            user_id=str(user.id),
        )
