"""Абстракция файлового хранилища.

Сейчас реализован только локальный диск (`LocalFileStorage`). Доменный код
(сервис материалов) работает через протокол `FileStorage`, поэтому позже хранилище
можно заменить на S3/MinIO без изменений в сервисе.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import anyio
from fastapi import UploadFile

_CHUNK_SIZE = 1024 * 1024  # 1 МБ


class StorageLimitExceeded(Exception):
    """Размер загружаемого файла превысил лимит."""


class FileStorage(Protocol):
    """Протокол файлового хранилища (диск, S3, …)."""

    async def save(self, key: str, upload: UploadFile, *, max_bytes: int | None = None) -> int:
        """Сохранить файл по ключу, вернуть размер в байтах."""
        ...

    def open_stream(self, key: str) -> Iterator[bytes]:
        """Открыть файл на чтение чанками (для StreamingResponse)."""
        ...

    async def delete(self, key: str) -> None:
        """Удалить файл по ключу (молча, если его нет)."""
        ...


class LocalFileStorage:
    """Хранилище на локальном диске под базовой директорией."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)

    def _resolve(self, key: str) -> Path:
        """Путь к файлу с защитой от выхода за пределы base (path traversal)."""
        base = self._base.resolve()
        path = (base / key).resolve()
        if path != base and base not in path.parents:
            raise ValueError("Недопустимый ключ хранилища")
        return path

    async def save(self, key: str, upload: UploadFile, *, max_bytes: int | None = None) -> int:
        path = self._resolve(key)
        await anyio.to_thread.run_sync(lambda: path.parent.mkdir(parents=True, exist_ok=True))
        handle = await anyio.to_thread.run_sync(lambda: path.open("wb"))
        size = 0
        try:
            while True:
                chunk = await upload.read(_CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if max_bytes is not None and size > max_bytes:
                    raise StorageLimitExceeded
                await anyio.to_thread.run_sync(handle.write, chunk)
        except StorageLimitExceeded:
            await anyio.to_thread.run_sync(handle.close)
            await self.delete(key)
            raise
        finally:
            if not handle.closed:
                await anyio.to_thread.run_sync(handle.close)
        return size

    def open_stream(self, key: str) -> Iterator[bytes]:
        path = self._resolve(key)

        def _iter() -> Iterator[bytes]:
            with path.open("rb") as handle:
                while True:
                    chunk = handle.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    yield chunk

        return _iter()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        await anyio.to_thread.run_sync(lambda: path.unlink(missing_ok=True))
