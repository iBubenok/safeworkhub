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
async def test_subscription_guard_blocks_writes_allows_reads(
    client: AsyncClient,
    db_session,
    unique_email: str,
):
    """Неактивная подписка блокирует запись (SUBSCRIPTION_INACTIVE), но не чтение."""
    tokens, cookies = await register_and_login(client, unique_email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Материал создаётся, пока подписка активна (триал).
    created = await client.post(
        "/api/v1/materials",
        json={"title": "Инструкция", "content": "текст", "type": "article", "status": "published"},
        headers=headers,
        cookies=cookies,
    )
    assert created.status_code == 201, created.text

    subscription = await db_session.scalar(
        select(Subscription).where(Subscription.organization_id == tokens["organization_id"])
    )
    assert subscription is not None
    subscription.status = SubscriptionStatus.BLOCKED
    await db_session.flush()

    # Чтение доступно даже при неактивной подписке.
    read = await client.get("/api/v1/materials", headers=headers, cookies=cookies)
    assert read.status_code == 200, read.text

    # Запись блокируется с распознаваемым кодом.
    write = await client.post(
        "/api/v1/materials",
        json={"title": "Новая", "content": "x", "type": "article", "status": "draft"},
        headers=headers,
        cookies=cookies,
    )
    assert write.status_code == 403, write.text
    assert write.json()["error"]["code"] == "SUBSCRIPTION_INACTIVE"


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
async def test_create_news_rejects_javascript_source_url(
    client: AsyncClient,
    unique_email: str,
):
    """source_url с опасной схемой (javascript:) отклоняется — защита от XSS."""
    tokens, cookies = await register_and_login(client, unique_email)
    created = await client.post(
        "/api/v1/materials/news",
        json={
            "title": "Вредоносная новость",
            "content": "Текст",
            "status": "published",
            "source_url": "javascript:alert(document.cookie)",
        },
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 422, created.text


@pytest.mark.asyncio
async def test_create_news_rejects_javascript_cover_image_url(
    client: AsyncClient,
    unique_email: str,
):
    """cover_image_url с опасной схемой тоже отклоняется."""
    tokens, cookies = await register_and_login(client, unique_email)
    created = await client.post(
        "/api/v1/materials/news",
        json={
            "title": "Вредоносная обложка",
            "content": "Текст",
            "status": "published",
            "cover_image_url": "javascript:alert(1)",
        },
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 422, created.text


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


@pytest.mark.asyncio
async def test_search_in_drafts_returns_own_and_excludes_published(
    client: AsyncClient,
    unique_email: str,
):
    """Поиск с status=draft находит свой черновик и не возвращает опубликованные."""
    tokens, cookies = await register_and_login(client, unique_email)
    await create_article(client, tokens, cookies, title="Черновик про молотки", content="молоток", status="draft")
    await create_article(
        client, tokens, cookies, title="Опубликовано про молотки", content="молоток", status="published"
    )

    resp = await client.get(
        "/api/v1/materials/search",
        params={"q": "молоток", "status": "draft"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    titles = [item["title"] for item in resp.json()["items"]]
    assert "Черновик про молотки" in titles
    assert "Опубликовано про молотки" not in titles


@pytest.mark.asyncio
async def test_search_drafts_is_private(
    client: AsyncClient,
    db_session,
    unique_email: str,
):
    """Чужой черновик не находится поиском у участника, но находится у суперпользователя."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    await create_article(client, owner_tokens, owner_cookies, title="Секрет про каски", content="каска", status="draft")

    member_email = f"member_{unique_email}"
    member_tokens, member_cookies = await create_member_and_login(client, owner_tokens, owner_cookies, member_email)

    # участник (не автор) — не находит
    resp = await client.get(
        "/api/v1/materials/search",
        params={"q": "каска", "status": "draft"},
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["items"] == []

    # делаем участника суперпользователем — находит
    await db_session.execute(update(User).where(User.email == member_email).values(is_superuser=True))
    await db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": member_email, "password": "MemberPass123!"},
    )
    assert login.status_code == 200, login.text
    resp2 = await client.get(
        "/api/v1/materials/search",
        params={"q": "каска", "status": "draft"},
        headers=auth_headers(login.json()),
        cookies=login.cookies,
    )
    assert resp2.status_code == 200, resp2.text
    titles = [item["title"] for item in resp2.json()["items"]]
    assert "Секрет про каски" in titles


async def create_template(client: AsyncClient, tokens, cookies, **overrides) -> dict:
    payload = {"title": "Шаблон акта", "status": "published"}
    payload.update(overrides)
    resp = await client.post(
        "/api/v1/materials/templates",
        json=payload,
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def upload_file(
    client: AsyncClient, tokens, cookies, material_id, name="form.txt", data=b"hello", ctype="text/plain"
):
    return await client.post(
        f"/api/v1/materials/{material_id}/attachments",
        files={"file": (name, data, ctype)},
        headers=auth_headers(tokens),
        cookies=cookies,
    )


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient, unique_email: str):
    """Шаблон создаётся с типом template и пустым списком вложений."""
    tokens, cookies = await register_and_login(client, unique_email)
    body = await create_template(client, tokens, cookies, title="Шаблон приказа", summary="Бланк")
    assert body["type"] == "template"
    assert body["attachments"] == []


@pytest.mark.asyncio
async def test_upload_and_download_attachment(client: AsyncClient, unique_email: str):
    """Файл прикрепляется, виден в материале и скачивается как attachment."""
    tokens, cookies = await register_and_login(client, unique_email)
    template = await create_template(client, tokens, cookies)

    uploaded = await upload_file(client, tokens, cookies, template["id"], name="бланк.txt", data=b"fill me")
    assert uploaded.status_code == 201, uploaded.text
    att = uploaded.json()
    assert att["filename"] == "бланк.txt"
    assert att["size_bytes"] == len(b"fill me")

    fetched = await client.get(
        f"/api/v1/materials/{template['id']}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert fetched.status_code == 200, fetched.text
    assert [a["id"] for a in fetched.json()["attachments"]] == [att["id"]]

    download = await client.get(
        f"/api/v1/materials/{template['id']}/attachments/{att['id']}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert download.status_code == 200, download.text
    assert download.content == b"fill me"
    assert "attachment" in download.headers["content-disposition"]


@pytest.mark.asyncio
async def test_upload_rejects_disallowed_extension(client: AsyncClient, unique_email: str):
    """Файл с неразрешённым расширением отклоняется."""
    tokens, cookies = await register_and_login(client, unique_email)
    template = await create_template(client, tokens, cookies)
    resp = await upload_file(
        client, tokens, cookies, template["id"], name="evil.exe", data=b"MZ", ctype="application/octet-stream"
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_upload_rejects_oversize(client: AsyncClient, unique_email: str, monkeypatch):
    """Файл больше лимита отклоняется (лимит занижен через настройки)."""
    monkeypatch.setattr("app.core.config.settings.max_upload_size_mb", 0)
    tokens, cookies = await register_and_login(client, unique_email)
    template = await create_template(client, tokens, cookies)
    resp = await upload_file(client, tokens, cookies, template["id"], data=b"not empty")
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_attachment_upload_requires_owner_role(client: AsyncClient, unique_email: str):
    """Участник (не владелец) не может прикреплять файлы."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    template = await create_template(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )
    resp = await upload_file(client, member_tokens, member_cookies, template["id"])
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_attachment_download_privacy(client: AsyncClient, db_session, unique_email: str):
    """Вложение черновика не качается участником, но качается суперпользователем."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    template = await create_template(client, owner_tokens, owner_cookies, status="draft")
    uploaded = await upload_file(client, owner_tokens, owner_cookies, template["id"])
    att_id = uploaded.json()["id"]

    member_email = f"member_{unique_email}"
    member_tokens, member_cookies = await create_member_and_login(client, owner_tokens, owner_cookies, member_email)
    denied = await client.get(
        f"/api/v1/materials/{template['id']}/attachments/{att_id}",
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert denied.status_code == 404, denied.text

    await db_session.execute(update(User).where(User.email == member_email).values(is_superuser=True))
    await db_session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": member_email, "password": "MemberPass123!"},
    )
    allowed = await client.get(
        f"/api/v1/materials/{template['id']}/attachments/{att_id}",
        headers=auth_headers(login.json()),
        cookies=login.cookies,
    )
    assert allowed.status_code == 200, allowed.text


@pytest.mark.asyncio
async def test_published_attachment_downloadable_by_member(client: AsyncClient, unique_email: str):
    """Вложение опубликованного шаблона доступно участнику организации."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    template = await create_template(client, owner_tokens, owner_cookies, status="published")
    uploaded = await upload_file(client, owner_tokens, owner_cookies, template["id"])
    att_id = uploaded.json()["id"]

    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )
    resp = await client.get(
        f"/api/v1/materials/{template['id']}/attachments/{att_id}",
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_delete_material_removes_attachments(client: AsyncClient, unique_email: str):
    """Удаление материала убирает и вложения (скачивание становится 404)."""
    tokens, cookies = await register_and_login(client, unique_email)
    template = await create_template(client, tokens, cookies)
    uploaded = await upload_file(client, tokens, cookies, template["id"])
    att_id = uploaded.json()["id"]

    deleted = await client.request(
        "DELETE",
        f"/api/v1/materials/{template['id']}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert deleted.status_code == 204, deleted.text

    gone = await client.get(
        f"/api/v1/materials/{template['id']}/attachments/{att_id}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert gone.status_code == 404, gone.text


@pytest.mark.asyncio
async def test_create_npa_with_detail_fields(client: AsyncClient, unique_email: str):
    """НПА создаётся с метаданными и возвращает блок npa; деталь видна при чтении."""
    tokens, cookies = await register_and_login(client, unique_email)
    created = await client.post(
        "/api/v1/materials/npa",
        json={
            "title": "Трудовой кодекс Российской Федерации",
            "summary": "Раздел X. Охрана труда",
            "status": "published",
            "act_kind": "code",
            "level": "federal",
            "act_status": "in_force",
            "document_number": "197-ФЗ",
            "adoption_date": "2001-12-30",
            "effective_date": "2002-02-01",
            "issuing_authority": "Государственная Дума",
            "official_source_url": "https://pravo.gov.ru/tk",
        },
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["type"] == "npa"
    assert body["npa"]["act_kind"] == "code"
    assert body["npa"]["level"] == "federal"
    assert body["npa"]["act_status"] == "in_force"
    assert body["npa"]["document_number"] == "197-ФЗ"

    fetched = await client.get(
        f"/api/v1/materials/{body['id']}",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert fetched.status_code == 200, fetched.text
    npa = fetched.json()["npa"]
    assert npa["issuing_authority"] == "Государственная Дума"
    assert npa["official_source_url"] == "https://pravo.gov.ru/tk"


@pytest.mark.asyncio
async def test_create_npa_minimal(client: AsyncClient, unique_email: str):
    """Минимальный НПА — только название и вид акта."""
    tokens, cookies = await register_and_login(client, unique_email)
    created = await client.post(
        "/api/v1/materials/npa",
        json={"title": "Локальная инструкция по ОТ", "status": "published", "act_kind": "local_act"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["npa"]["act_kind"] == "local_act"
    assert body["npa"]["level"] is None
    assert body["npa"]["document_number"] is None


@pytest.mark.asyncio
async def test_create_npa_requires_act_kind(client: AsyncClient, unique_email: str):
    """Без вида акта создание НПА отклоняется (422)."""
    tokens, cookies = await register_and_login(client, unique_email)
    resp = await client.post(
        "/api/v1/materials/npa",
        json={"title": "Без вида", "status": "published"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_npa_rejects_javascript_source_url(client: AsyncClient, unique_email: str):
    """official_source_url с опасной схемой отклоняется."""
    tokens, cookies = await register_and_login(client, unique_email)
    resp = await client.post(
        "/api/v1/materials/npa",
        json={
            "title": "Вредоносный НПА",
            "status": "published",
            "act_kind": "federal_law",
            "official_source_url": "javascript:alert(1)",
        },
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 422, resp.text


async def get_versions(client: AsyncClient, tokens, cookies, material_id):
    resp = await client.get(
        f"/api/v1/materials/{material_id}/versions",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    return resp


@pytest.mark.asyncio
async def test_create_makes_first_version(client: AsyncClient, unique_email: str):
    """При создании материала появляется версия v1 со снимком."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies, title="Версия один", content="первый текст")
    resp = await get_versions(client, tokens, cookies, article["id"])
    assert resp.status_code == 200, resp.text
    versions = resp.json()
    assert len(versions) == 1
    assert versions[0]["version_no"] == 1
    assert versions[0]["snapshot"]["content"] == "первый текст"
    assert versions[0]["editor_name"] == "Материаловед"


@pytest.mark.asyncio
async def test_edit_creates_new_version_with_note(client: AsyncClient, unique_email: str):
    """Правка контента создаёт v2 с примечанием; история по убыванию версий."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies, content="старый")
    patch = await client.patch(
        f"/api/v1/materials/{article['id']}",
        json={"content": "новый", "change_note": "обновил текст"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 200, patch.text

    versions = (await get_versions(client, tokens, cookies, article["id"])).json()
    assert [v["version_no"] for v in versions] == [2, 1]
    assert versions[0]["snapshot"]["content"] == "новый"
    assert versions[0]["change_note"] == "обновил текст"
    assert versions[1]["snapshot"]["content"] == "старый"


@pytest.mark.asyncio
async def test_noop_edit_creates_no_version(client: AsyncClient, unique_email: str):
    """Пустая правка не создаёт новую версию."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies, content="текст")
    await client.patch(
        f"/api/v1/materials/{article['id']}",
        json={"content": "текст"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    versions = (await get_versions(client, tokens, cookies, article["id"])).json()
    assert len(versions) == 1


@pytest.mark.asyncio
async def test_status_only_change_creates_no_version(client: AsyncClient, unique_email: str):
    """Архивация (смена статуса) не создаёт версию."""
    tokens, cookies = await register_and_login(client, unique_email)
    article = await create_article(client, tokens, cookies, status="published")
    archived = await client.post(
        f"/api/v1/materials/{article['id']}/archive",
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert archived.status_code == 200, archived.text
    versions = (await get_versions(client, tokens, cookies, article["id"])).json()
    assert len(versions) == 1


@pytest.mark.asyncio
async def test_version_history_is_private(client: AsyncClient, db_session, unique_email: str):
    """Историю чужого черновика не видит участник, но видит суперпользователь."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    article = await create_article(client, owner_tokens, owner_cookies, status="draft")

    member_email = f"member_{unique_email}"
    member_tokens, member_cookies = await create_member_and_login(client, owner_tokens, owner_cookies, member_email)
    denied = await get_versions(client, member_tokens, member_cookies, article["id"])
    assert denied.status_code == 404, denied.text

    await db_session.execute(update(User).where(User.email == member_email).values(is_superuser=True))
    await db_session.commit()
    login = await client.post("/api/v1/auth/login", json={"email": member_email, "password": "MemberPass123!"})
    allowed = await get_versions(client, login.json(), login.cookies, article["id"])
    assert allowed.status_code == 200, allowed.text
    assert len(allowed.json()) == 1


async def create_npa(client: AsyncClient, tokens, cookies, **overrides) -> dict:
    payload = {"title": "Акт", "status": "published", "act_kind": "federal_law"}
    payload.update(overrides)
    resp = await client.post("/api/v1/materials/npa", json=payload, headers=auth_headers(tokens), cookies=cookies)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_update_npa_changes_fields(client: AsyncClient, unique_email: str):
    """PATCH /npa меняет реквизиты НПА."""
    tokens, cookies = await register_and_login(client, unique_email)
    npa = await create_npa(client, tokens, cookies)
    patch = await client.patch(
        f"/api/v1/materials/{npa['id']}/npa",
        json={"act_status": "repealed", "document_number": "426-ФЗ", "issuing_authority": "Госдума"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 200, patch.text
    body = patch.json()
    assert body["npa"]["act_status"] == "repealed"
    assert body["npa"]["document_number"] == "426-ФЗ"
    assert body["npa"]["issuing_authority"] == "Госдума"


@pytest.mark.asyncio
async def test_npa_supersedes_link_forward_and_reverse(client: AsyncClient, unique_email: str):
    """Установка replaced_by даёт прямую ссылку у старого и обратную у нового."""
    tokens, cookies = await register_and_login(client, unique_email)
    old = await create_npa(client, tokens, cookies, title="Старый акт")
    new = await create_npa(client, tokens, cookies, title="Новый акт")

    patch = await client.patch(
        f"/api/v1/materials/{old['id']}/npa",
        json={"act_status": "repealed", "replaced_by_id": new["id"]},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["npa"]["replaced_by"]["id"] == new["id"]
    assert patch.json()["npa"]["replaced_by"]["title"] == "Новый акт"

    new_resp = await client.get(f"/api/v1/materials/{new['id']}", headers=auth_headers(tokens), cookies=cookies)
    replaces = new_resp.json()["npa"]["replaces"]
    assert [r["id"] for r in replaces] == [old["id"]]
    assert replaces[0]["title"] == "Старый акт"


@pytest.mark.asyncio
async def test_npa_cannot_replace_self(client: AsyncClient, unique_email: str):
    """Акт не может ссылаться на самого себя."""
    tokens, cookies = await register_and_login(client, unique_email)
    npa = await create_npa(client, tokens, cookies)
    resp = await client.patch(
        f"/api/v1/materials/{npa['id']}/npa",
        json={"replaced_by_id": npa["id"]},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_npa_replacement_must_be_npa(client: AsyncClient, unique_email: str):
    """Документ-замена должен быть НПА (не статья)."""
    tokens, cookies = await register_and_login(client, unique_email)
    npa = await create_npa(client, tokens, cookies)
    article = await create_article(client, tokens, cookies)
    resp = await client.patch(
        f"/api/v1/materials/{npa['id']}/npa",
        json={"replaced_by_id": article["id"]},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_npa_update_creates_no_version(client: AsyncClient, unique_email: str):
    """Правка реквизитов НПА не создаёт новую версию."""
    tokens, cookies = await register_and_login(client, unique_email)
    npa = await create_npa(client, tokens, cookies)
    await client.patch(
        f"/api/v1/materials/{npa['id']}/npa",
        json={"act_status": "amended"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    versions = (await get_versions(client, tokens, cookies, npa["id"])).json()
    assert len(versions) == 1


@pytest.mark.asyncio
async def test_npa_update_requires_owner(client: AsyncClient, unique_email: str):
    """Участник (не владелец) не может править реквизиты НПА."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    npa = await create_npa(client, owner_tokens, owner_cookies)
    member_tokens, member_cookies = await create_member_and_login(
        client, owner_tokens, owner_cookies, f"member_{unique_email}"
    )
    resp = await client.patch(
        f"/api/v1/materials/{npa['id']}/npa",
        json={"act_status": "repealed"},
        headers=auth_headers(member_tokens),
        cookies=member_cookies,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_npa_replacement_nulled_on_delete(client: AsyncClient, unique_email: str):
    """Удаление акта-замены обнуляет ссылку (SET NULL)."""
    tokens, cookies = await register_and_login(client, unique_email)
    old = await create_npa(client, tokens, cookies, title="Старый")
    new = await create_npa(client, tokens, cookies, title="Новый")
    await client.patch(
        f"/api/v1/materials/{old['id']}/npa",
        json={"replaced_by_id": new["id"]},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    deleted = await client.request(
        "DELETE", f"/api/v1/materials/{new['id']}", headers=auth_headers(tokens), cookies=cookies
    )
    assert deleted.status_code == 204, deleted.text
    old_resp = await client.get(f"/api/v1/materials/{old['id']}", headers=auth_headers(tokens), cookies=cookies)
    assert old_resp.json()["npa"]["replaced_by"] is None


@pytest.mark.asyncio
async def test_owner_cannot_set_public_visibility(client: AsyncClient, unique_email: str):
    """Владелец без суперпользователя не может сделать материал публичным ни при создании, ни при правке."""
    tokens, cookies = await register_and_login(client, unique_email)
    created = await client.post(
        "/api/v1/materials/articles",
        json={"title": "Публичная статья", "content": "текст", "status": "published", "visibility": "public"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert created.status_code == 403, created.text

    article = await create_article(client, tokens, cookies)  # visibility=org по умолчанию
    updated = await client.patch(
        f"/api/v1/materials/{article['id']}",
        json={"visibility": "public"},
        headers=auth_headers(tokens),
        cookies=cookies,
    )
    assert updated.status_code == 403, updated.text


@pytest.mark.asyncio
async def test_superuser_can_set_public_visibility(client: AsyncClient, db_session, unique_email: str):
    """Суперпользователь может создать публичный материал."""
    await register_and_login(client, unique_email)
    await db_session.execute(update(User).where(User.email == unique_email).values(is_superuser=True))
    await db_session.commit()
    relogin = await client.post("/api/v1/auth/login", json={"email": unique_email, "password": "MaterialPass123!"})
    su_tokens, su_cookies = relogin.json(), relogin.cookies

    created = await create_article(client, su_tokens, su_cookies, title="Публичная от суперюзера", visibility="public")
    assert created["visibility"] == "public"
