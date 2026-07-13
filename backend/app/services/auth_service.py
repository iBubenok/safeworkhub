"""Сервис аутентификации и регистрации."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    generate_session_family,
    get_password_hash,
    hash_token,
    verify_password,
    verify_token,
)
from app.db.repositories import (
    OrganizationRepository,
    RefreshSessionRepository,
    SubscriptionRepository,
    TariffRepository,
    UserRepository,
)
from app.models import OrganizationUser, OrgRole, SubscriptionStatus, Tariff
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserResponse
from app.services.utils import utcnow


class AuthService:
    """Сервис аутентификации и управления refresh-сессиями."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.org_repo = OrganizationRepository(session)
        self.refresh_repo = RefreshSessionRepository(session)
        self.tariff_repo = TariffRepository(session)
        self.subscription_repo = SubscriptionRepository(session)

    async def _ensure_default_tariff(self) -> Tariff:
        tariff = await self.tariff_repo.get_by_code(settings.default_tariff_code)
        if tariff:
            return tariff
        return await self.tariff_repo.create(
            code=settings.default_tariff_code,
            name="Базовый",
            description="Базовый тариф для пробного периода",
            max_users=25,
            price_monthly=0,
            price_yearly=0,
            features={
                "materials": True,
                "courses": True,
                "search": True,
            },
            is_active=True,
        )

    async def register(self, data: RegisterRequest) -> RegisterResponse:
        """Регистрация новой организации с владельцем."""
        if await self.user_repo.is_email_taken(data.admin_email):
            raise EmailAlreadyExistsError(data.admin_email)

        if await self.org_repo.is_inn_taken(data.inn):
            raise ConflictError(
                message="Организация с таким ИНН уже зарегистрирована",
                field="inn",
            )

        tariff = await self._ensure_default_tariff()
        organization = await self.org_repo.create(
            name=data.organization_name,
            inn=data.inn,
            description=None,
        )
        user = await self.user_repo.create(
            email=data.admin_email.lower(),
            password_hash=get_password_hash(data.admin_password),
            name=data.admin_name,
            is_active=True,
            primary_organization_id=organization.id,
            password_changed_at=utcnow(),
        )

        await self.user_repo.add_membership(
            user_id=user.id,
            organization_id=organization.id,
            role=OrgRole.ORG_OWNER,
        )
        await self.org_repo.set_owner(organization.id, user.id)

        trial_end = utcnow() + timedelta(days=settings.subscription_trial_days)
        subscription = await self.subscription_repo.create(
            organization_id=organization.id,
            tariff_id=tariff.id,
            status=SubscriptionStatus.TRIAL,
            valid_until=trial_end,
            trial_ends_at=trial_end,
        )

        return RegisterResponse(
            organization_id=organization.id,
            user_id=user.id,
            subscription_status=subscription.status,
            trial_ends_at=subscription.trial_ends_at,
        )

    async def _resolve_membership(self, user_id: UUID, organization_id: int | None) -> OrganizationUser:
        """Получить актуальное членство пользователя."""
        user = await self.user_repo.get_with_memberships(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        memberships = [m for m in user.organization_memberships if m.is_active]
        if not memberships:
            raise InvalidCredentialsError()

        if organization_id:
            for membership in memberships:
                if membership.organization_id == organization_id:
                    return membership
            raise InvalidCredentialsError()

        return memberships[0]

    async def login(
        self,
        data: LoginRequest,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> TokenResponse:
        """Аутентификация пользователя и выдача пары токенов."""
        user = await self.user_repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError()

        membership = await self._resolve_membership(user.id, data.organization_id)

        organization_id = membership.organization_id
        org_role = membership.role if isinstance(membership.role, OrgRole) else OrgRole(membership.role)
        roles = ["admin"] if user.is_superuser else [org_role.value]

        session_id, family_id = generate_session_family()
        refresh_token = create_refresh_token(
            user.id,
            session_id=session_id,
            family_id=family_id,
        )
        await self.refresh_repo.create_session(
            session_id=session_id,
            user_id=user.id,
            family_id=family_id,
            token_hash=hash_token(refresh_token),
            expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )

        access_token = create_access_token(
            user.id,
            organization_id=organization_id,
            roles=roles,
        )

        user.last_login_at = utcnow()
        user.primary_organization_id = organization_id

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_expires_in=settings.refresh_token_expire_days * 24 * 60 * 60,
            organization_id=organization_id,
            role=org_role.value,
            user=UserResponse.model_validate(user),
            refresh_token=refresh_token,
        )

    async def refresh_tokens(
        self,
        refresh_token: str,
        *,
        user_agent: str | None,
        ip_address: str | None,
    ) -> TokenResponse:
        """Ротация токенов с проверкой повторного использования."""
        payload = verify_token(refresh_token, TokenType.REFRESH)
        if payload is None or payload.sid is None or payload.fam is None:
            raise InvalidCredentialsError()

        session = await self.refresh_repo.get_by_id(payload.sid)
        token_hash = hash_token(refresh_token)

        if (
            session is None
            or session.revoked_at is not None
            or session.token_hash != token_hash
            or session.expires_at <= utcnow()
        ):
            if payload.fam:
                await self.refresh_repo.revoke_family(payload.fam)
            raise InvalidCredentialsError()

        user = await self.user_repo.get_by_id(payload.sub)
        if user is None or not user.is_active:
            raise InvalidCredentialsError()

        membership = await self._resolve_membership(user.id, user.primary_organization_id)
        organization_id = membership.organization_id
        org_role = membership.role if isinstance(membership.role, OrgRole) else OrgRole(membership.role)
        roles = ["admin"] if user.is_superuser else [org_role.value]

        new_session_id = generate_session_family()[0]
        new_refresh_token = create_refresh_token(
            user.id,
            session_id=new_session_id,
            family_id=session.family_id,
        )

        await self.refresh_repo.revoke(session.id, replaced_by=new_session_id)
        await self.refresh_repo.create_session(
            session_id=new_session_id,
            user_id=user.id,
            family_id=session.family_id,
            token_hash=hash_token(new_refresh_token),
            expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
        )

        access_token = create_access_token(
            user.id,
            organization_id=organization_id,
            roles=roles,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_expires_in=settings.refresh_token_expire_days * 24 * 60 * 60,
            organization_id=organization_id,
            role=org_role.value,
            user=UserResponse.model_validate(user),
            refresh_token=new_refresh_token,
        )

    async def logout(self, refresh_token: str | None) -> None:
        """Отозвать refresh-сессию пользователя."""
        if not refresh_token:
            return

        payload = verify_token(refresh_token, TokenType.REFRESH)
        if payload is None or payload.sid is None:
            return

        await self.refresh_repo.revoke(payload.sid)
