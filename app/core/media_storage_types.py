"""B7.4C: media storage types (core — safe for ``Settings`` import graph)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MediaStorageBackend(StrEnum):
    """Configured via ``MEDIA_STORAGE_BACKEND``."""

    DISABLED = "disabled"
    MEMORY = "memory"
    S3_COMPATIBLE = "s3_compatible"


class MediaSourceKind(StrEnum):
    """Classification of ``cover_media_reference`` / source string for ingestion."""

    EMPTY = "empty"
    TELEGRAM_PHOTO = "telegram_photo"
    HTTPS_URL = "https_url"
    HTTP_URL = "http_url"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class StoredObject:
    object_key: str
    content_type: str
    byte_size: int
    etag: str | None
    metadata: dict[str, str]
