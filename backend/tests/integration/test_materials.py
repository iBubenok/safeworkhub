"""Интеграционные тесты для базы знаний и ограничений подписки."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.models import Subscription, SubscriptionStatus, User


def build_registration_payload(email: str) -> dict:
    return {
        "organization_name": "Организация материалов",
        "inn": "1653001806",
        "admin_email": email,
        "admin_password": "MaterialPass123!",
        "admin_name": "Материаловед",
    }


async def register_and_login(client: AsyncClient, email: str, inn: str | None = None):
    payload = build_registration_payload(email)
    if inn:
        payload["inn"] = inn
    register = await client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201
    auth = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["admin_email"], "password": payload["admin_password"]},
    )
    assert auth.status_code == 200
    tokens = auth.json()
    return tokens, auth.cookies


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def create_article(client: AsyncClient, tokens, cookies, **overrides) -> dict:
    payload = {"title": "Статья", "content": "Текст статьи", "status": "published"}
    payload.update(overrides)
    resp = await client.post(
        "/api/v1/materials/articles",
        json=payload,
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_member_and_login(client: AsyncClient, owner_tokens, owner_cookies, email: str):
    """Создать участника той же организации (роль member) и залогиниться им."""
    created = await client.post(
        "/api/v1/users",
        json={"email": email, "name": "Сотрудник", "password": "MemberPass123!", "role": "member"},
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    assert created.status_code == 201, created.text
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "MemberPass123!"},
    )
    assert login.status_code == 200, login.text
    return login.json(), login.cookies


@pytest.mark.asyncio
async def test_subscription_guard_blocks_materials_when_inactive(
    client: AsyncClient,
    db_session,
    unique_email: str,
):
    """Проверка, что неактивная подписка блокирует доступ к материалам."""
    tokens, cookies = await register_and_login(client, unique_email)

    subscription = await db_session.scalar(
        select(Subscription).where(Subscription.organization_id == tokens["organization_id"])
    )
    assert subscription is not None
    subscription.status = SubscriptionStatus.BLOCKED
    await db_session.flush()

    response = await client.get(
        "/api/v1/materials",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        cookies=cookies,
    )
    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "AUTHORIZATION_ERROR"


@pytest.mark.asyncio
async def test_materials_search_and_listing(
    client: AsyncClient,
    unique_email: str,
):
    """Создание и поиск материалов с публикацией и FTS."""
    tokens, cookies = await register_and_login(client, unique_email)

    create_payload = {
        "title": "Инструкция по безопасности на производстве",
        "summary": "Краткое описание инструкции",
        "content": "Полный текст инструкции по охране труда и безопасности.",
        "type": "article",
        "status": "published",
        "category_id": None,
    }
    created = await client.post(
        "/api/v1/materials",
        json=create_payload,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    material_id = created.json()["id"]

    search = await client.get(
        "/api/v1/materials/search",
        params={"q": "безопасности"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        cookies=cookies,
    )
    assert search.status_code == 200
    data = search.json()
    assert data["total"] >= 1
    assert any(item["id"] == material_id for item in data["items"])


@pytest.mark.asyncio
async def test_create_article_markdown_and_view_draft(
    client: AsyncClient,
    unique_email: str,
):
    """Создание статьи (Markdown, черновик) и её просмотр автором до публикации."""
    tokens, cookies = await register_and_login(client, unique_email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_payload = {
        "title": "Как провести вводный инструктаж",
        "summary": "Пошаговый гайд",
        "content": "## Шаги\n\n1. Подготовить программу\n2. Провести\n3. Зафиксировать",
        "status": "draft",
    }
    created = await client.post(
        "/api/v1/materials/articles",
        json=create_payload,
        headers=headers,
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["type"] == "article"
    assert body["content_format"] == "markdown"
    assert body["status"] == "draft"
    article_id = body["id"]

    # Черновик доступен для просмотра автору/организации (после правки get_material).
    fetched = await client.get(
        f"/api/v1/materials/{article_id}",
        headers=headers,
        cookies=cookies,
    )
    assert fetched.status_code == 200, fetched.text
    detail = fetched.json()
    assert detail["content"].startswith("## Шаги")
    assert detail["content_format"] == "markdown"


@pytest.mark.asyncio
async def test_view_published_article_increments_views(
    client: AsyncClient,
    unique_email: str,
):
    """Просмотр опубликованной статьи отдаёт 200 и увеличивает счётчик просмотров."""
    tokens, cookies = await register_and_login(client, unique_email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    created = await client.post(
        "/api/v1/materials/articles",
        json={"title": "Опубликованная", "content": "## Текст", "status": "published"},
        headers=headers,
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    article_id = created.json()["id"]

    first = await client.get(f"/api/v1/materials/{article_id}", headers=headers, cookies=cookies)
    assert first.status_code == 200, first.text

    second = await client.get(f"/api/v1/materials/{article_id}", headers=headers, cookies=cookies)
    assert second.status_code == 200
    assert second.json()["views_count"] >= 1


@pytest.mark.asyncio
async def test_get_material_returns_author_and_organization(
    client: AsyncClient,
    unique_email: str,
):
    """Детальный ответ содержит имя автора и название организации."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies)

    resp = await client.get(f"/api/v1/materials/{article['id']}", headers=auth_headers(tokens), cookies=cookies)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["author_name"] == "Материаловед"
    assert data["organization_name"] == "Организация материалов"


@pytest.mark.asyncio
async def test_view_does_not_change_updated_at(
    client: AsyncClient,
    unique_email: str,
):
    """Просмотр увеличивает счётчик, но не двигает дату изменения."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies)

    # несколько просмотров
    for _ in range(2):
        await client.get(f"/api/v1/materials/{article['id']}", headers=auth_headers(tokens), cookies=cookies)
    resp = await client.get(f"/api/v1/materials/{article['id']}", headers=auth_headers(tokens), cookies=cookies)
    data = resp.json()
    assert data["created_at"] == data["updated_at"]
    assert data["updated_by_name"] is None
    assert data["views_count"] >= 1


@pytest.mark.asyncio
async def test_update_article_records_editor_and_change_time(
    client: AsyncClient,
    unique_email: str,
):
    """Реальная правка меняет контент, дату изменения и фиксирует редактора."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies, content="старый текст")

    patch = await client.patch(
        f"/api/v1/materials/{article['id']}",
        json={"content": "## Новый\n\nтекст"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 200, patch.text

    resp = await client.get(f"/api/v1/materials/{article['id']}", headers=auth_headers(tokens), cookies=cookies)
    data = resp.json()
    assert data["content"].startswith("## Новый")
    assert data["created_at"] != data["updated_at"]
    assert data["updated_by_name"] == "Материаловед"


@pytest.mark.asyncio
async def test_update_article_noop_keeps_unmodified(
    client: AsyncClient,
    unique_email: str,
):
    """Сохранение без фактических изменений не помечает статью изменённой."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies, title="Без правок", content="тело")

    patch = await client.patch(
        f"/api/v1/materials/{article['id']}",
        json={"title": "Без правок", "content": "тело"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 200, patch.text

    resp = await client.get(f"/api/v1/materials/{article['id']}", headers=auth_headers(tokens), cookies=cookies)
    data = resp.json()
    assert data["created_at"] == data["updated_at"]
    assert data["updated_by_name"] is None


@pytest.mark.asyncio
async def test_update_article_only_author(
    client: AsyncClient,
    unique_email: str,
):
    """Редактировать статью может только автор: участник той же организации получает 403."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    article = await create_article(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )

    resp = await client.patch(
        f"/api/v1/materials/{article['id']}",
        json={"content": "чужая правка"},
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_archive_article_hides_from_listing(
    client: AsyncClient,
    unique_email: str,
):
    """Архивация переводит в archived, прячет из списка, но автор статью видит."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies, title="В архив")

    archived = await client.post(
        f"/api/v1/materials/{article['id']}/archive",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert archived.status_code == 200, archived.text
    assert archived.json()["status"] == "archived"

    listing = await client.get("/api/v1/materials", headers=auth_headers(tokens), cookies=cookies)
    titles = [item["title"] for item in listing.json()["items"]]
    assert "В архив" not in titles

    detail = await client.get(f"/api/v1/materials/{article['id']}", headers=auth_headers(tokens), cookies=cookies)
    assert detail.status_code == 200


@pytest.mark.asyncio
async def test_archive_article_only_author(
    client: AsyncClient,
    unique_email: str,
):
    """Архивировать может только автор."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    article = await create_article(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )

    resp = await client.post(
        f"/api/v1/materials/{article['id']}/archive",
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_delete_article_then_not_found(
    client: AsyncClient,
    unique_email: str,
):
    """Удаление возвращает 204, после чего материал недоступен."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies)

    deleted = await client.request(
        "DELETE",
        f"/api/v1/materials/{article['id']}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert deleted.status_code == 204, deleted.text

    resp = await client.get(f"/api/v1/materials/{article['id']}", headers=auth_headers(tokens), cookies=cookies)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_article_only_author(
    client: AsyncClient,
    unique_email: str,
):
    """Удалить статью может только автор."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    article = await create_article(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )

    resp = await client.request(
        "DELETE",
        f"/api/v1/materials/{article['id']}",
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_list_drafts_returns_own_and_excludes_published(
    client: AsyncClient,
    unique_email: str,
):
    """Раздел «Черновики» отдаёт черновики автора и не содержит опубликованных."""
    tokens, cookies = await register_and_login(client, unique_email)
    await create_article(client, tokens, cookies, title="Черновик", status="draft")
    await create_article(client, tokens, cookies, title="Опубликованная", status="published")

    resp = await client.get(
        "/api/v1/materials",
        params={"status": "draft"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    titles = [item["title"] for item in resp.json()["items"]]
    assert "Черновик" in titles
    assert "Опубликованная" not in titles


@pytest.mark.asyncio
async def test_list_archived_returns_archived(
    client: AsyncClient,
    unique_email: str,
):
    """Раздел «Архив» отдаёт архивные материалы."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies, title="Будет в архиве")
    await client.post(
        f"/api/v1/materials/{article['id']}/archive",
        headers=auth_headers(tokens),
        cookies=cookies,
    )

    resp = await client.get(
        "/api/v1/materials",
        params={"status": "archived"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    titles = [item["title"] for item in resp.json()["items"]]
    assert "Будет в архиве" in titles


@pytest.mark.asyncio
async def test_drafts_not_visible_to_other_org(
    client: AsyncClient,
    unique_email: str,
):
    """Черновики одной организации не видны владельцу другой организации."""
    owner_a, cookies_a = await register_and_login(client, unique_email)
    await create_article(client, owner_a, cookies_a, title="Секретный черновик A", status="draft")

    owner_b, cookies_b = await register_and_login(client, f"b_{unique_email}", inn="9999999999")
    resp = await client.get(
        "/api/v1/materials",
        params={"status": "draft"},
        headers=auth_headers(owner_b),
        cookies=cookies_b,
    )
    assert resp.status_code == 200, resp.text
    titles = [item["title"] for item in resp.json()["items"]]
    assert "Секретный черновик A" not in titles


@pytest.mark.asyncio
async def test_member_does_not_see_owner_drafts(
    client: AsyncClient,
    unique_email: str,
):
    """Участник организации (не автор) не видит чужие черновики."""
    owner, cookies = await register_and_login(client, unique_email)
    await create_article(client, owner, cookies, title="Черновик владельца", status="draft")
    member_tokens, member_cookies = await create_member_and_login(client, owner, cookies, f"member_{unique_email}")

    resp = await client.get(
        "/api/v1/materials",
        params={"status": "draft"},
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_superuser_sees_org_drafts(
    client: AsyncClient,
    db_session,
    unique_email: str,
):
    """Суперпользователь видит черновики всех авторов организации."""
    owner, cookies = await register_and_login(client, unique_email)
    await create_article(client, owner, cookies, title="Черновик для супера", status="draft")

    member_email = f"super_{unique_email}"
    await create_member_and_login(client, owner, cookies, member_email)
    # Делаем участника суперпользователем и перелогиниваемся, чтобы токен это отражал.
    await db_session.execute(update(User).where(User.email == member_email).values(is_superuser=True))
    await db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": member_email, "password": "MemberPass123!"},
    )
    assert login.status_code == 200, login.text

    resp = await client.get(
        "/api/v1/materials",
        params={"status": "draft"},
        headers=auth_headers(login.json()),
        cookies=login.cookies,
    )
    assert resp.status_code == 200, resp.text
    titles = [item["title"] for item in resp.json()["items"]]
    assert "Черновик для супера" in titles


@pytest.mark.asyncio
async def test_restore_archived_to_draft(
    client: AsyncClient,
    unique_email: str,
):
    """Восстановление возвращает архивный материал в черновик."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies)
    await client.post(
        f"/api/v1/materials/{article['id']}/archive",
        headers=auth_headers(tokens),
        cookies=cookies,
    )

    restored = await client.post(
        f"/api/v1/materials/{article['id']}/restore",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_restore_only_author(
    client: AsyncClient,
    unique_email: str,
):
    """Восстанавливать из архива может только автор."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    article = await create_article(client, owner_tokens, owner_cookies)
    await client.post(
        f"/api/v1/materials/{article['id']}/archive",
        headers=auth_headers(owner_tokens),
        cookies=owner_cookies,
    )
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )

    resp = await client.post(
        f"/api/v1/materials/{article['id']}/restore",
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_draft_not_viewable_by_other_member(
    client: AsyncClient,
    unique_email: str,
):
    """Чужой черновик нельзя открыть по прямой ссылке (даже члену той же организации)."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    draft = await create_article(client, owner_tokens, owner_cookies, status="draft")
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )

    resp = await client.get(
        f"/api/v1/materials/{draft['id']}",
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 404, resp.text


@pytest.mark.asyncio
async def test_superuser_can_view_any_draft(
    client: AsyncClient,
    db_session,
    unique_email: str,
):
    """Суперпользователь может открыть чужой черновик по ссылке."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    draft = await create_article(client, owner_tokens, owner_cookies, status="draft")

    member_email = f"super_{unique_email}"
    await create_member_and_login(client, owner_tokens, owner_cookies, member_email)
    await db_session.execute(update(User).where(User.email == member_email).values(is_superuser=True))
    await db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": member_email, "password": "MemberPass123!"},
    )
    assert login.status_code == 200, login.text

    resp = await client.get(
        f"/api/v1/materials/{draft['id']}",
        headers=auth_headers(login.json()),
        cookies=login.cookies,
    )
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_create_article_with_html_format(
    client: AsyncClient,
    unique_email: str,
):
    """Статью можно создать в формате HTML."""
    tokens, cookies = await register_and_login(client, unique_email)
    created = await client.post(
        "/api/v1/materials/articles",
        json={"title": "HTML-статья", "content": "<h2>Привет</h2>", "content_format": "html"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    assert created.json()["content_format"] == "html"

    fetched = await client.get(
        f"/api/v1/materials/{created.json()['id']}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["content_format"] == "html"
    assert fetched.json()["content"] == "<h2>Привет</h2>"


@pytest.mark.asyncio
async def test_update_changes_content_format(
    client: AsyncClient,
    unique_email: str,
):
    """Редактирование может сменить формат тела (markdown → html)."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies)  # markdown по умолчанию

    patch = await client.patch(
        f"/api/v1/materials/{article['id']}",
        json={"content": "<p>Теперь HTML</p>", "content_format": "html"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 200, patch.text

    fetched = await client.get(
        f"/api/v1/materials/{article['id']}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert fetched.json()["content_format"] == "html"


@pytest.mark.asyncio
async def test_create_news_with_detail_fields(
    client: AsyncClient,
    unique_email: str,
):
    """Новость создаётся с источником, датой, обложкой и тегами."""
    tokens, cookies = await register_and_login(client, unique_email)
    created = await client.post(
        "/api/v1/materials/news",
        json={
            "title": "Новый приказ Минтруда",
            "content": "Краткое содержание",
            "status": "published",
            "source_url": "https://mintrud.gov.example/order-123",
            "event_date": "2026-05-10",
            "cover_image_url": "https://example.com/cover.png",
            "tags": ["охрана труда", "приказ"],
        },
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["type"] == "news"
    assert body["news"]["source_url"] == "https://mintrud.gov.example/order-123"
    assert body["news"]["event_date"] == "2026-05-10"
    assert body["news"]["cover_image_url"] == "https://example.com/cover.png"
    assert body["news"]["tags"] == ["охрана труда", "приказ"]

    fetched = await client.get(
        f"/api/v1/materials/{body['id']}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["news"]["tags"] == ["охрана труда", "приказ"]


@pytest.mark.asyncio
async def test_create_minimal_news(
    client: AsyncClient,
    unique_email: str,
):
    """Лёгкая новость — только заголовок и текст; деталь с пустыми полями."""
    tokens, cookies = await register_and_login(client, unique_email)
    created = await client.post(
        "/api/v1/materials/news",
        json={"title": "Появился новый виджет", "content": "Описание", "status": "published"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["type"] == "news"
    assert body["news"]["source_url"] is None
    assert body["news"]["tags"] == []
