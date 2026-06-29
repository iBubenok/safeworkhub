"""Интеграционные тесты подмодуля «Проверки» (проведение проверки по чек-листу)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def register_and_login(
    client: AsyncClient, email: str, *, org_name: str = "Орг проверок", inn: str = "1653001806"
):
    payload = {
        "organization_name": org_name,
        "inn": inn,
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
        "title": "Проверка рабочего места",
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


async def start_run(client: AsyncClient, tokens, cookies, checklist_id: str, **overrides) -> dict:
    payload = {"checklist_id": checklist_id}
    payload.update(overrides)
    resp = await client.post("/api/v1/checklist-runs", json=payload, headers=auth_headers(tokens), cookies=cookies)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_start_run_snapshots_items(client: AsyncClient, unique_email: str):
    """Старт проверки разворачивает дерево шаблона в плоские снимки пунктов (с разделами)."""
    tokens, cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(
        client,
        tokens,
        cookies,
        title="Древовидный",
        items=[
            {
                "node_type": "group",
                "text": "Документы",
                "children": [
                    {"node_type": "item", "text": "Наряд-допуск", "answer_type": "compliance"},
                    {"node_type": "item", "text": "Журнал инструктажа", "answer_type": "yes_no"},
                ],
            },
            {"node_type": "item", "text": "Замечания", "answer_type": "text"},
        ],
    )
    run = await start_run(client, tokens, cookies, checklist["id"])
    assert run["status"] == "in_progress"
    assert run["checklist_title"] == "Древовидный"
    assert [a["item_text"] for a in run["answers"]] == ["Наряд-допуск", "Журнал инструктажа", "Замечания"]
    # Раздел сохраняется как group_title у вложенных пунктов.
    assert run["answers"][0]["group_title"] == "Документы"
    assert run["answers"][2]["group_title"] is None
    assert all(a["value"] is None for a in run["answers"])


@pytest.mark.asyncio
async def test_cannot_start_from_draft(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    draft = await create_checklist(client, tokens, cookies, status="draft")
    resp = await client.post(
        "/api/v1/checklist-runs",
        json={"checklist_id": draft["id"]},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_member_can_conduct_run(client: AsyncClient, unique_email: str):
    """Проводить проверку может любой участник (не только владелец)."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )
    run = await start_run(client, member_tokens, member_cookies, checklist["id"])
    assert run["status"] == "in_progress"


@pytest.mark.asyncio
async def test_fill_and_complete_scoring(client: AsyncClient, unique_email: str):
    """Заполнение и завершение считают итог: соответствие 1 из 2 → 50%, есть нарушения; н/п исключается."""
    tokens, cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(
        client,
        tokens,
        cookies,
        items=[
            {"text": "Пункт 1", "answer_type": "compliance"},
            {"text": "Пункт 2", "answer_type": "compliance"},
            {"text": "Пункт 3", "answer_type": "compliance"},
            {"text": "Комментарий", "answer_type": "text"},
        ],
    )
    run = await start_run(client, tokens, cookies, checklist["id"])
    by_text = {a["item_text"]: a["id"] for a in run["answers"]}

    patch = await client.patch(
        f"/api/v1/checklist-runs/{run['id']}",
        json={
            "answers": [
                {"answer_id": by_text["Пункт 1"], "value": "compliant"},
                {"answer_id": by_text["Пункт 2"], "value": "non_compliant", "comment": "нет ограждения"},
                {"answer_id": by_text["Пункт 3"], "value": "not_applicable"},
                {"answer_id": by_text["Комментарий"], "value": "всё прочее в норме"},
            ]
        },
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 200, patch.text
    saved = patch.json()
    assert saved["status"] == "in_progress"
    assert saved["gradable_count"] == 3
    assert saved["compliant_count"] == 1
    assert saved["non_compliant_count"] == 1
    assert saved["not_applicable_count"] == 1
    assert saved["score"] == 50.0

    done = await client.post(
        f"/api/v1/checklist-runs/{run['id']}/complete", headers=auth_headers(tokens), cookies=cookies
    )
    assert done.status_code == 200, done.text
    body = done.json()
    assert body["status"] == "completed"
    assert body["result"] == "has_issues"
    assert body["score"] == 50.0
    assert body["completed_at"] is not None


@pytest.mark.asyncio
async def test_completed_run_is_read_only(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, tokens, cookies)
    run = await start_run(client, tokens, cookies, checklist["id"])
    await client.post(f"/api/v1/checklist-runs/{run['id']}/complete", headers=auth_headers(tokens), cookies=cookies)

    patch = await client.patch(
        f"/api/v1/checklist-runs/{run['id']}",
        json={"notes": "поздняя правка"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 409, patch.text


@pytest.mark.asyncio
async def test_run_visible_to_whole_org(client: AsyncClient, unique_email: str):
    """Проверку видят все участники организации, а не только проводящий."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, owner_tokens, owner_cookies)
    run = await start_run(client, owner_tokens, owner_cookies, checklist["id"], title="Проверка склада")

    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )
    detail = await client.get(
        f"/api/v1/checklist-runs/{run['id']}", headers=auth_headers(member_tokens), cookies=member_cookies
    )
    assert detail.status_code == 200, detail.text
    lst = await client.get("/api/v1/checklist-runs", headers=auth_headers(member_tokens), cookies=member_cookies)
    assert run["id"] in [r["id"] for r in lst.json()["items"]]


@pytest.mark.asyncio
async def test_run_isolated_by_organization(client: AsyncClient, unique_email: str):
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    checklist = await create_checklist(client, owner_tokens, owner_cookies)
    run = await start_run(client, owner_tokens, owner_cookies, checklist["id"])

    other_tokens, other_cookies = await register_and_login(
        client, f"other_{unique_email}", org_name="Другая орг", inn="7707083893"
    )
    denied = await client.get(
        f"/api/v1/checklist-runs/{run['id']}", headers=auth_headers(other_tokens), cookies=other_cookies
    )
    assert denied.status_code == 404, denied.text
    lst = await client.get("/api/v1/checklist-runs", headers=auth_headers(other_tokens), cookies=other_cookies)
    assert lst.json()["total"] == 0


@pytest.mark.asyncio
async def test_start_run_unknown_checklist(client: AsyncClient, unique_email: str):
    tokens, cookies = await register_and_login(client, unique_email)
    resp = await client.post(
        "/api/v1/checklist-runs",
        json={"checklist_id": str(uuid.uuid4())},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 404, resp.text
