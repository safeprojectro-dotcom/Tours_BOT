"""B7.4C: conservative media storage foundation (config, adapter, no real S3 / getFile)."""

from __future__ import annotations

from app.core.media_storage_types import (
    MediaSourceKind,
    MediaStorageBackend,
    StoredObject,
)
from .adapter import (
    DisabledMediaStorageAdapter,
    InMemoryMediaStorageAdapter,
    MediaStorageAdapter,
    MediaStorageDisabledError,
    MediaStorageNotImplementedError,
    get_media_storage_adapter,
)

__all__ = [
    "DisabledMediaStorageAdapter",
    "InMemoryMediaStorageAdapter",
    "MediaSourceKind",
    "MediaStorageAdapter",
    "MediaStorageBackend",
    "MediaStorageDisabledError",
    "MediaStorageNotImplementedError",
    "StoredObject",
    "get_media_storage_adapter",
]
