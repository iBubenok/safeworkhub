"""
Тесты модуля безопасности.

Проверяет корректность работы хеширования паролей и JWT токенов.
"""

import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenPayload,
)
from app.core.config import settings


class TestPasswordHashing:
    """Тесты хеширования паролей."""

    def test_hash_password_creates_hash(self):
        """Хеширование создаёт хеш, отличающийся от исходного пароля."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Правильный пароль проходит проверку."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Неправильный пароль не проходит проверку."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_unique(self):
        """Каждый вызов создаёт уникальный хеш (разные соли)."""
        password = "SecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Тесты JWT токенов."""

    def test_create_access_token(self):
        """Создание access токена с правильными данными."""
        user_id = "test-user-id"
        token = create_access_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Создание access токена с кастомным временем жизни."""
        user_id = "test-user-id"
        expires_delta = timedelta(hours=1)
        token = create_access_token(subject=user_id, expires_delta=expires_delta)

        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        assert decoded["sub"] == user_id
        assert "exp" in decoded

    def test_create_refresh_token(self):
        """Создание refresh токена."""
        user_id = "test-user-id"
        token = create_refresh_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self):
        """Декодирование валидного токена."""
        user_id = "test-user-id"
        token = create_access_token(subject=user_id)

        payload = decode_token(token)

        assert payload is not None
        assert payload.sub == user_id

    def test_decode_token_invalid(self):
        """Декодирование невалидного токена возвращает None."""
        invalid_token = "invalid.token.here"

        payload = decode_token(invalid_token)

        assert payload is None

    def test_decode_token_wrong_secret(self):
        """Токен, подписанный другим ключом, не декодируется."""
        user_id = "test-user-id"

        # Создаём токен с "неправильным" ключом
        wrong_token = jwt.encode(
            {"sub": user_id, "exp": 9999999999},
            "wrong-secret-key",
            algorithm="HS256",
        )

        payload = decode_token(wrong_token)

        assert payload is None

    def test_access_and_refresh_tokens_different(self):
        """Access и refresh токены для одного пользователя различаются."""
        user_id = "test-user-id"

        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)

        assert access_token != refresh_token
