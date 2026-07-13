"""Интеграционные тесты для курсов и назначений."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient


def build_registration_payload(email: str) -> dict:
    return {
        "organization_name": "Учебный центр",
        "inn": "5406575752",
        "admin_email": email,
        "admin_password": "OwnerPass123!",
        "admin_name": "Владелец Курсов",
    }


async def register_and_login(client: AsyncClient, email: str):
    payload = build_registration_payload(email)
    register = await client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["admin_email"], "password": payload["admin_password"]},
    )
    assert login.status_code == 200
    return login.json(), login.cookies


async def create_member(
    client: AsyncClient,
    owner_tokens: dict,
    cookies,
    email: str,
) -> dict:
    payload = {
        "name": "Сотрудник",
        "email": email,
        "password": "MemberPass123!",
        "role": "member",
    }
    response = await client.post(
        "/api/v1/users",
        json=payload,
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
        cookies=cookies,
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_course_assignment_and_progress(client: AsyncClient, unique_email: str):
    """Создание курса, назначение пользователю и фиксация прогресса."""
    owner_tokens, owner_cookies = await register_and_login(client, unique_email)
    member_email = f"member_{uuid4().hex}@example.com"
    member = await create_member(client, owner_tokens, owner_cookies, member_email)

    # Логин под членом организации
    member_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": member_email,
            "password": "MemberPass123!",
            "organization_id": owner_tokens["organization_id"],
        },
    )
    assert member_login.status_code == 200
    member_tokens = member_login.json()

    course_payload = {
        "title": "Курс по охране труда",
        "description": "Базовый курс",
        "content": "# Введение\n\nТекст курса, фото и видео.",
        "duration_minutes": 90,
        "is_published": False,
    }
    course_resp = await client.post(
        "/api/v1/courses",
        json=course_payload,
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
        cookies=owner_cookies,
    )
    assert course_resp.status_code == 201, course_resp.text
    course_id = course_resp.json()["id"]
    assert course_resp.json()["content"] == "# Введение\n\nТекст курса, фото и видео."

    # Курс доступен по прямой ссылке с содержимым.
    got = await client.get(
        f"/api/v1/courses/{course_id}",
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
        cookies=owner_cookies,
    )
    assert got.status_code == 200, got.text
    assert got.json()["content"] == "# Введение\n\nТекст курса, фото и видео."

    publish = await client.post(
        f"/api/v1/courses/{course_id}/publish",
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
        cookies=owner_cookies,
    )
    assert publish.status_code == 200

    assign = await client.post(
        f"/api/v1/courses/{course_id}/assign",
        json={"user_ids": [member["id"]]},
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
        cookies=owner_cookies,
    )
    assert assign.status_code == 200, assign.text
    assert len(assign.json()) == 1

    progress = await client.post(
        f"/api/v1/courses/{course_id}/progress",
        params={"progress_percent": 100},
        headers={"Authorization": f"Bearer {member_tokens['access_token']}"},
        cookies=member_login.cookies,
    )
    assert progress.status_code == 200
    progress_data = progress.json()
    assert progress_data["status"] == "completed"
    assert progress_data["progress_percent"] == 100
