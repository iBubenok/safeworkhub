"""Интеграционные тесты подмодуля «Чек-листы»."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models import User


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def register_and_login(client: AsyncClient, email: str):
    payload = {
        "organization_name": "Организация чек-листов",
        "inn": "1653001806",
        "admin_email": email,
        "admin_password": "CheckPass123!",
        "admin_name": "Проверяющий",
    }
    register = await client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201, register.text
    auth = await client.post("/api/v1/auth/login", json={"email": email, "password": payload["admin_password"]})
    assert auth.status_code == 200, auth.text
    return auth.json(), auth.cookies


async def create_member_and_login(client: AsyncClient, owner_tokens, owner_cookies, email: str):
    created = await client.post(
        "/api/v1/users",
        json={"email": email, "name": "Сотрудник", "password": "MemberPass123!", "role": "member"},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    assert created.status_code == 201, created.text
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "MemberPass123!"})
    assert login.status_code == 200, login.text
    return login.json(), login.cookies


async def create_checklist(client: AsyncClient, tokens, cookies, **overrides) -> dict:
    payload = {
        "title": "Чек-лист по работе на высоте",
        "status": "published",
        "items": [
            {"text": "Наличие наряда-допуска", "answer_type": "compliance", "required": True},
            {"text": "Исправность СИЗ", "answer_type": "yes_no", "required": True},
        ],
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/checklists", json=payload, headers=auth_headers(tokens), cookies=cookies)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_create_checklist(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    body = await create_checklist(client, tokens, cookies)
    assert body["status"] == "published"
    assert len(body["items"]) == 2
    assert body["items"][0]["answer_type"] == "compliance"
    assert body["items"][0]["node_type"] == "item"
    assert body["items"][0]["children"] == []


@pytest.mark.asyncio
async def test_create_tree_and_read_nested(client: AsyncClient, unique_email: str):
    """Дерево (раздел → подраздел → пункты) создаётся и читается вложенным; item_count считает пункты."""
    tokens, cookies = await register_and_login(client, unique_email)
    payload = {
        "title": "Работа на высоте",
        "status": "published",
        "items": [
            {
                "node_type": "group",
                "text": "Главное",
                "children": [
                    {
                        "node_type": "group",
                        "text": "Охрана труда",
                        "children": [
                            {"node_type": "item", "text": "Наряд-допуск", "answer_type": "compliance"},
                            {"node_type": "item", "text": "СИЗ", "answer_type": "yes_no"},
                        ],
                    },
                ],
            },
            {"node_type": "item", "text": "Прочее", "answer_type": "text"},
        ],
    }
    created = await client.post("/api/v1/checklists", json=payload, headers=auth_headers(tokens), cookies=cookies)
    assert created.status_code == 201, created.text
    body = created.json()
    # Верхний уровень: группа «Главное» + пункт «Прочее».
    assert [n["node_type"] for n in body["items"]] == ["group", "item"]
    glavnoe = body["items"][0]
    assert glavnoe["text"] == "Главное"
    ot = glavnoe["children"][0]
    assert ot["node_type"] == "group" and ot["text"] == "Охрана труда"
    assert [c["text"] for c in ot["children"]] == ["Наряд-допуск", "СИЗ"]

    # В списке item_count — только пункты (3), группы не считаются.
    lst = await client.get("/api/v1/checklists", headers=auth_headers(tokens), cookies=cookies)
    card = next(c for c in lst.json()["items"] if c["id"] == body["id"])
    assert card["item_count"] == 3


@pytest.mark.asyncio
async def test_group_without_answer_type_ok_item_without_rejected(client: AsyncClient, unique_email: str):
    """Группа без типа ответа валидна; пункт без типа ответа — 422."""
    tokens, cookies = await register_and_login(client, unique_email)
    ok = await client.post(
        "/api/v1/checklists",
        json={
            "title": "С разделом",
            "status": "draft",
            "items": [
                {
                    "node_type": "group",
                    "text": "Раздел",
                    "children": [{"node_type": "item", "text": "П", "answer_type": "yes_no"}],
                }
            ],
        },
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert ok.status_code == 201, ok.text

    bad = await client.post(
        "/api/v1/checklists",
        json={"title": "Битый пункт", "status": "draft", "items": [{"node_type": "item", "text": "Без типа"}]},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert bad.status_code == 422, bad.text


@pytest.mark.asyncio
async def test_member_cannot_create(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )
    resp = await client.post(
        "/api/v1/checklists",
        json={"title": "x", "items": []},
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_member_sees_only_published(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    await create_checklist(client, owner_tokens, owner_cookies, title="Опубликованный", status="published")
    await create_checklist(client, owner_tokens, owner_cookies, title="Черновик", status="draft")

    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )
    resp = await client.get("/api/v1/checklists", headers=auth_headers(member_tokens), cookies=member_cookies)
    assert resp.status_code == 200, resp.text
    titles = [c["title"] for c in resp.json()["items"]]
    assert "Опубликованный" in titles
    assert "Черновик" not in titles

    # Владелец видит и черновики.
    owner_resp = await client.get("/api/v1/checklists", headers=auth_headers(owner_tokens), cookies=owner_cookies)
    owner_titles = [c["title"] for c in owner_resp.json()["items"]]
    assert "Черновик" in owner_titles


@pytest.mark.asyncio
async def test_draft_detail_is_private(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    draft = await create_checklist(client, owner_tokens, owner_cookies, status="draft")
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )
    denied = await client.get(
        f"/api/v1/checklists/{draft['id']}", headers=auth_headers(member_tokens), cookies=member_cookies
    )
    assert denied.status_code == 404, denied.text
    allowed = await client.get(
        f"/api/v1/checklists/{draft['id']}", headers=auth_headers(owner_tokens), cookies=owner_cookies
    )
    assert allowed.status_code == 200, allowed.text


@pytest.mark.asyncio
async def test_update_replaces_items(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, tokens, cookies)
    patch = await client.patch(
        f"/api/v1/checklists/{checklist['id']}",
        json={"title": "Обновлённый", "items": [{"text": "Единственный пункт", "answer_type": "text"}]},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 200, patch.text
    body = patch.json()
    assert body["title"] == "Обновлённый"
    assert len(body["items"]) == 1
    assert body["items"][0]["text"] == "Единственный пункт"


@pytest.mark.asyncio
async def test_publish_and_archive(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, tokens, cookies, status="draft")
    pub = await client.post(
        f"/api/v1/checklists/{checklist['id']}/publish", headers=auth_headers(tokens), cookies=cookies
    )
    assert pub.status_code == 200 and pub.json()["status"] == "published", pub.text
    arch = await client.post(
        f"/api/v1/checklists/{checklist['id']}/archive", headers=auth_headers(tokens), cookies=cookies
    )
    assert arch.status_code == 200 and arch.json()["status"] == "archived", arch.text


@pytest.mark.asyncio
async def test_item_reference_to_material(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    article = await client.post(
        "/api/v1/materials/articles",
        json={"title": "Правила работы на высоте", "content": "текст", "status": "published"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert article.status_code == 201, article.text
    material_id = article.json()["id"]

    body = await create_checklist(
        client,
        tokens,
        cookies,
        items=[
            {
                "text": "Соблюдены правила",
                "answer_type": "compliance",
                "reference_material_id": material_id,
                "reference_note": "п. 5",
            }
        ],
    )
    assert body["items"][0]["reference_material_id"] == material_id
    assert body["items"][0]["reference_material_title"] == "Правила работы на высоте"
    assert body["items"][0]["reference_note"] == "п. 5"


@pytest.mark.asyncio
async def test_item_reference_unknown_material_rejected(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    resp = await client.post(
        "/api/v1/checklists",
        json={
            "title": "Битая ссылка",
            "status": "draft",
            "items": [{"text": "Вопрос", "answer_type": "text", "reference_material_id": str(uuid.uuid4())}],
        },
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_superuser_sees_drafts(client: AsyncClient, db_session, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    await create_checklist(client, owner_tokens, owner_cookies, title="Чужой черновик", status="draft")

    member_email = f"member_{unique_email}"
    await create_member_and_login(client, owner_tokens, owner_cookies, member_email)
    await db_session.execute(update(User).where(User.email == member_email).values(is_superuser=True))
    await db_session.commit()
    login = await client.post("/api/v1/auth/login", json={"email": member_email, "password": "MemberPass123!"})
    resp = await client.get("/api/v1/checklists", headers=auth_headers(login.json()), cookies=login.cookies)
    titles = [c["title"] for c in resp.json()["items"]]
    assert "Чужой черновик" in titles
