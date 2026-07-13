"""Интеграционные тесты смены пароля (свой пароль и установка админом)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models import User


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def register_and_login(client: AsyncClient, email: str, *, inn: str = "1653001806"):
    payload = {
        "organization_name": "Орг паролей",
        "inn": inn,
        "admin_email": email,
        "admin_password": "OwnerPass123!",
        "admin_name": "Владелец",
    }
    reg = await client.post("/api/v1/auth/register", json=payload)
    assert reg.status_code == 201, reg.text
    auth = await client.post("/api/v1/auth/login", json={"email": email, "password": "OwnerPass123!"})
    assert auth.status_code == 200, auth.text
    return auth.json(), auth.cookies


async def create_user(client, owner_tokens, owner_cookies, email: str, role: str = "member") -> str:
    resp = await client.post(
        "/api/v1/users",
        json={"email": email, "name": "Юзер", "password": "InitPass123!", "role": role},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def login(client, email: str, password: str):
    return await client.post("/api/v1/auth/login", json={"email": email, "password": password})


@pytest.mark.asyncio
async def test_change_own_password(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    resp = await client.post(
        "/api/v1/users/me/password",
        json={"current_password": "OwnerPass123!", "new_password": "BrandNew123!"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 204, resp.text
    # Новый пароль работает, старый — нет.
    assert (await login(client, unique_email, "BrandNew123!")).status_code == 200
    assert (await login(client, unique_email, "OwnerPass123!")).status_code == 401
    # password_changed_at проставлен.
    me = await client.get("/api/v1/users/me", headers=auth_headers(tokens), cookies=cookies)
    assert me.json()["password_changed_at"] is not None


@pytest.mark.asyncio
async def test_change_own_password_wrong_current(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    resp = await client.post(
        "/api/v1/users/me/password",
        json={"current_password": "WrongOld1!", "new_password": "BrandNew123!"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_owner_sets_member_password(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    member_email = f"member_{unique_email}"
    member_id = await create_user(client, owner_tokens, owner_cookies, member_email, role="member")

    resp = await client.post(
        f"/api/v1/users/{member_id}/password",
        json={"new_password": "MemberNew123!"},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    assert resp.status_code == 204, resp.text
    assert (await login(client, member_email, "MemberNew123!")).status_code == 200
    assert (await login(client, member_email, "InitPass123!")).status_code == 401


@pytest.mark.asyncio
async def test_owner_cannot_set_other_owner_password(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    other_owner_id = await create_user(client, owner_tokens, owner_cookies, f"owner2_{unique_email}", role="org_owner")
    resp = await client.post(
        f"/api/v1/users/{other_owner_id}/password",
        json={"new_password": "Nope12345!"},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_member_cannot_set_others_password(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    member_email = f"member_{unique_email}"
    await create_user(client, owner_tokens, owner_cookies, member_email, role="member")
    victim_id = await create_user(client, owner_tokens, owner_cookies, f"victim_{unique_email}", role="member")
    member_login = await login(client, member_email, "InitPass123!")
    member_tokens = member_login.json()

    resp = await client.post(
        f"/api/v1/users/{victim_id}/password",
        json={"new_password": "Hacked123!"},
        headers=auth_headers(member_tokens),
        cookies=member_login.cookies,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_admin_endpoint_rejects_self(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    me = await client.get("/api/v1/users/me", headers=auth_headers(tokens), cookies=cookies)
    own_id = me.json()["id"]
    resp = await client.post(
        f"/api/v1/users/{own_id}/password",
        json={"new_password": "SelfViaAdmin1!"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_superuser_sets_owner_password(client: AsyncClient, db_session, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    owner_email = unique_email

    su_email = f"su_{unique_email}"
    await create_user(client, owner_tokens, owner_cookies, su_email, role="member")
    await db_session.execute(update(User).where(User.email == su_email).values(is_superuser=True))
    await db_session.commit()
    su_login = await login(client, su_email, "InitPass123!")
    su_tokens = su_login.json()

    me = await client.get("/api/v1/users/me", headers=auth_headers(owner_tokens), cookies=owner_cookies)
    owner_id = me.json()["id"]

    resp = await client.post(
        f"/api/v1/users/{owner_id}/password",
        json={"new_password": "OwnerReset123!"},
        headers=auth_headers(su_tokens),
        cookies=su_login.cookies,
    )
    assert resp.status_code == 204, resp.text
    assert (await login(client, owner_email, "OwnerReset123!")).status_code == 200
