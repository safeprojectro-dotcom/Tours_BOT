"""B7.4C: storage adapter protocol, disabled + in-memory implementations, factory."""

from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable

from app.core.config import Settings, get_settings

from app.core.media_storage_types import MediaStorageBackend, StoredObject


class MediaStorageDisabledError(RuntimeError):
    """Raised when ``MEDIA_STORAGE_BACKEND=disabled`` and a write is attempted."""


class MediaStorageNotImplementedError(NotImplementedError):
    """Raised when ``s3_compatible`` is selected (future slice)."""


@runtime_checkable
class MediaStorageAdapter(Protocol):
    def put_object(
        self,
        *,
        object_key: str,
        content_type: str,
        body: bytes,
        metadata: dict[str, str],
    ) -> StoredObject: ...

    def object_exists(self, *, object_key: str) -> bool: ...

    def public_url_for(self, *, object_key: str) -> str | None: ...

    def delete_object(self, *, object_key: str) -> None: ...


class DisabledMediaStorageAdapter:
    """No-op backend: reads report missing objects; writes raise."""

    def put_object(
        self,
        *,
        object_key: str,
        content_type: str,
        body: bytes,
        metadata: dict[str, str],
    ) -> StoredObject:
        raise MediaStorageDisabledError("MEDIA_STORAGE_BACKEND is disabled")

    def object_exists(self, *, object_key: str) -> bool:
        return False

    def public_url_for(self, *, object_key: str) -> str | None:
        return None

    def delete_object(self, *, object_key: str) -> None:
        return None


class InMemoryMediaStorageAdapter:
    """Process-local dict storage for tests and local dev when backend=memory."""

    def __init__(self, *, public_base_url: str | None = None) -> None:
        self._public_base_url = (public_base_url or "").rstrip("/")
        self._objects: dict[str, tuple[bytes, str, dict[str, str], str | None]] = {}

    def put_object(
        self,
        *,
        object_key: str,
        content_type: str,
        body: bytes,
        metadata: dict[str, str],
    ) -> StoredObject:
        etag = hashlib.sha256(body).hexdigest()
        self._objects[object_key] = (body, content_type, dict(metadata), etag)
        return StoredObject(
            object_key=object_key,
            content_type=content_type,
            byte_size=len(body),
            etag=etag,
            metadata=dict(metadata),
        )

    def object_exists(self, *, object_key: str) -> bool:
        return object_key in self._objects

    def public_url_for(self, *, object_key: str) -> str | None:
        if not self._public_base_url:
            return None
        return f"{self._public_base_url}/{object_key.lstrip('/')}"

    def delete_object(self, *, object_key: str) -> None:
        self._objects.pop(object_key, None)


def get_media_storage_adapter(settings: Settings | None = None) -> MediaStorageAdapter:
    """Return the adapter for the current ``MEDIA_STORAGE_BACKEND`` setting."""

    s = settings or get_settings()
    backend = s.media_storage_backend_parsed
    if backend is MediaStorageBackend.DISABLED:
        return DisabledMediaStorageAdapter()
    if backend is MediaStorageBackend.MEMORY:
        return InMemoryMediaStorageAdapter(public_base_url=s.media_storage_public_base_url)
    if backend is MediaStorageBackend.S3_COMPATIBLE:
        raise MediaStorageNotImplementedError(
            "MEDIA_STORAGE_BACKEND=s3_compatible is not implemented in B7.4C"
        )
    raise ValueError(f"Unknown MEDIA_STORAGE_BACKEND: {s.media_storage_backend!r}")
