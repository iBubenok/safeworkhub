"""Юнит-тесты функций безопасности."""

from __future__ import annotations

from uuid import uuid4

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_session_family,
    get_password_hash,
    hash_token,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Хеширование паролей Argon2."""

    def test_hash_and_verify_password(self):
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestTokenHandling:
    """Создание и проверка JWT токенов."""

    def test_access_token_contains_roles_and_org(self):
        user_id = uuid4()
        token = create_access_token(
            user_id,
            organization_id=42,
            roles=["member"],
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == user_id
        assert payload.org == 42
        assert payload.roles == ["member"]
        assert payload.type == TokenType.ACCESS

    def test_refresh_rotation_payload(self):
        user_id = uuid4()
        session_id, family_id = generate_session_family()
        refresh = create_refresh_token(
            user_id,
            session_id=session_id,
            family_id=family_id,
        )
        payload = verify_token(refresh, TokenType.REFRESH)
        assert payload is not None
        assert payload.sid == session_id
        assert payload.fam == family_id

    def test_hash_token_produces_stable_digest(self):
        raw = "refresh-token-value"
        digest = hash_token(raw)
        assert digest == hash_token(raw)
        assert digest != raw
