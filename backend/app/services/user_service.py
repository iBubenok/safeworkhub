"""Сервис для работы с пользователями."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
    EmailAlreadyExistsError,
    UserLimitExceededError,
    UserNotFoundError,
    ValidationError,
)
from app.core.security import get_password_hash, verify_password
from app.db.repositories import (
    OrganizationRepository,
    RefreshSessionRepository,
    SubscriptionRepository,
    UserRepository,
)
from app.models import OrgRole
from app.schemas.user import (
    MembershipResponse,
    OrgMemberOption,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserWithMemberships,
)
from app.services.utils import log_audit, utcnow


class UserService:
    """Сервис для работы с пользователями и их членствами."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
        self.refresh_repo = RefreshSessionRepository(session)

    async def _map_memberships(self, user_id: UUID) -> list[MembershipResponse]:
        user = await self.repository.get_with_memberships(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        memberships = [
            MembershipResponse(
                organization_id=m.organization_id,
                role=m.role.value if isinstance(m.role, OrgRole) else str(m.role),
                is_active=m.is_active,
                joined_at=m.joined_at,
            )
            for m in user.organization_memberships
        ]
        return memberships

    async def get_user(self, user_id: UUID) -> UserWithMemberships:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        memberships = await self._map_memberships(user_id)
        return UserWithMemberships(
            **UserResponse.model_validate(user).model_dump(),
            memberships=memberships,
        )

    async def create_user(
        self,
        data: UserCreate,
        *,
        organization_id: int,
        actor_id: UUID | None = None,
        request_id: str | None = None,
    ) -> UserWithMemberships:
        if await self.repository.is_email_taken(data.email):
            raise EmailAlreadyExistsError(data.email)

        subscription = await self.subscription_repo.get_with_tariff(organization_id)
        if subscription is None:
            raise UserLimitExceededError(limit=0)

        active_users = await self.organization_repo.get_users_count(organization_id)
        if subscription.tariff.max_users <= active_users:
            raise UserLimitExceededError(limit=subscription.tariff.max_users)

        user = await self.repository.create(
            email=data.email.lower(),
            password_hash=get_password_hash(data.password),
            name=data.name,
            is_active=True,
            primary_organization_id=organization_id,
            password_changed_at=utcnow(),
        )

        role = OrgRole(data.role) if data.role else OrgRole.MEMBER
        await self.repository.add_membership(
            user_id=user.id,
            organization_id=organization_id,
            role=role,
        )

        await log_audit(
            self.session,
            action="user_created",
            entity_type="user",
            entity_id=str(user.id),
            organization_id=organization_id,
            user_id=str(actor_id) if actor_id else None,
            request_id=request_id,
            details={"role": role.value},
        )

        memberships = await self._map_memberships(user.id)
        return UserWithMemberships(
            **UserResponse.model_validate(user).model_dump(),
            memberships=memberships,
        )

    async def update_user(
        self,
        user_id: UUID,
        organization_id: int,
        data: UserUpdate,
    ) -> UserWithMemberships:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        if (
            data.email
            and data.email.lower() != user.email
            and await self.repository.is_email_taken(data.email, exclude_user_id=user_id)
        ):
            raise EmailAlreadyExistsError(data.email)

        update_data = data.model_dump(exclude_unset=True)
        if "email" in update_data:
            update_data["email"] = update_data["email"].lower()

        updated_user = await self.repository.update(user_id, **update_data)

        if data.role:
            await self.repository.update_membership_role(
                user_id=user_id,
                organization_id=organization_id,
                role=OrgRole(data.role),
            )

        memberships = await self._map_memberships(user_id)
        return UserWithMemberships(
            **UserResponse.model_validate(updated_user).model_dump(),
            memberships=memberships,
        )

    async def deactivate_user(
        self,
        user_id: UUID,
        organization_id: int,
        *,
        actor_id: UUID | None = None,
        request_id: str | None = None,
    ) -> None:
        await self.repository.deactivate_membership(user_id, organization_id)
        await self.repository.update(user_id, is_active=False)
        await log_audit(
            self.session,
            action="user_deactivated",
            entity_type="user",
            entity_id=str(user_id),
            organization_id=organization_id,
            user_id=str(actor_id) if actor_id else str(user_id),
            request_id=request_id,
        )

    async def activate_user(
        self,
        user_id: UUID,
        organization_id: int,
        *,
        actor_id: UUID | None = None,
        request_id: str | None = None,
    ) -> None:
        await self.repository.activate_membership(user_id, organization_id)
        await self.repository.update(user_id, is_active=True)
        await log_audit(
            self.session,
            action="user_activated",
            entity_type="user",
            entity_id=str(user_id),
            organization_id=organization_id,
            user_id=str(actor_id) if actor_id else str(user_id),
            request_id=request_id,
        )

    async def list_org_members(self, organization_id: int) -> list[OrgMemberOption]:
        """Активные участники организации (минимум данных) — для выбора при назначении."""
        rows = await self.repository.get_by_organization(organization_id=organization_id)
        return [OrgMemberOption.model_validate(user) for user, _role in rows if user.is_active]

    async def search_users(
        self,
        organization_id: int,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[UserResponse]:
        rows = await self.repository.get_by_organization(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )
        needle = query.lower()
        return [
            UserResponse.model_validate(user).model_copy(
                update={"role": role.value if isinstance(role, OrgRole) else str(role)}
            )
            for user, role in rows
            if needle in user.email.lower() or needle in user.name.lower()
        ]

    async def change_own_password(
        self,
        user_id: UUID,
        *,
        organization_id: int,
        current_password: str,
        new_password: str,
        request_id: str | None = None,
    ) -> None:
        """Смена собственного пароля с проверкой текущего. Сессии не отзываются."""
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        if not verify_password(current_password, user.password_hash):
            raise ValidationError("Текущий пароль указан неверно")
        await self.repository.update(
            user_id,
            password_hash=get_password_hash(new_password),
            password_changed_at=utcnow(),
        )
        await log_audit(
            self.session,
            action="password_changed",
            entity_type="user",
            entity_id=str(user_id),
            organization_id=organization_id,
            user_id=str(user_id),
            request_id=request_id,
        )

    @staticmethod
    def _can_set_password(
        *,
        actor_role: OrgRole | str | None,
        actor_is_superuser: bool,
        target_role: OrgRole,
        target_is_superuser: bool,
    ) -> bool:
        """Кто кому может задать пароль: супер — любому; владелец — только сотрудникам."""
        if target_is_superuser and not actor_is_superuser:
            return False
        if actor_is_superuser:
            return True
        if actor_role == OrgRole.ORG_OWNER:
            return target_role == OrgRole.MEMBER
        return False

    async def set_user_password(
        self,
        target_id: UUID,
        *,
        organization_id: int,
        actor_id: UUID,
        actor_role: OrgRole | str | None,
        actor_is_superuser: bool,
        new_password: str,
        request_id: str | None = None,
    ) -> None:
        """Установить пароль другому пользователю организации (админ). Отзывает его сессии."""
        if target_id == actor_id:
            raise ValidationError("Свой пароль меняйте в разделе «Настройки»")
        target = await self.repository.get_by_id(target_id)
        membership = await self.repository.get_membership(target_id, organization_id)
        if target is None or membership is None:
            raise UserNotFoundError(str(target_id))
        if not self._can_set_password(
            actor_role=actor_role,
            actor_is_superuser=actor_is_superuser,
            target_role=membership.role,
            target_is_superuser=target.is_superuser,
        ):
            raise AuthorizationError("Недостаточно прав для смены пароля этого пользователя")
        await self.repository.update(
            target_id,
            password_hash=get_password_hash(new_password),
            password_changed_at=utcnow(),
        )
        # Принудительно завершаем сессии пользователя — старый пароль больше не действует.
        await self.refresh_repo.revoke_all_for_user(target_id)
        await log_audit(
            self.session,
            action="password_set_by_admin",
            entity_type="user",
            entity_id=str(target_id),
            organization_id=organization_id,
            user_id=str(actor_id),
            request_id=request_id,
        )
