"""Сервис для работы с пользователями."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailAlreadyExistsError,
    UserLimitExceededError,
    UserNotFoundError,
)
from app.core.security import get_password_hash
from app.db.repositories import (
    OrganizationRepository,
    SubscriptionRepository,
    UserRepository,
)
from app.models import OrgRole
from app.schemas.user import MembershipResponse, UserCreate, UserResponse, UserUpdate, UserWithMemberships
from app.services.utils import log_audit


class UserService:
    """Сервис для работы с пользователями и их членствами."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)
        self.organization_repo = OrganizationRepository(session)
        self.subscription_repo = SubscriptionRepository(session)

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

    async def search_users(
        self,
        organization_id: int,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[UserResponse]:
        users = await self.repository.get_by_organization(
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )
        filtered = [u for u in users if query.lower() in u.email.lower() or query.lower() in u.name.lower()]
        return [UserResponse.model_validate(u) for u in filtered]
