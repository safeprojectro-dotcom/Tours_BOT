"""B7.4C: media storage adapter (disabled + in-memory)."""

from __future__ import annotations

import unittest

from app.core.config import Settings
from app.core.media_storage_types import MediaStorageBackend
from app.services.media_storage import (
    DisabledMediaStorageAdapter,
    InMemoryMediaStorageAdapter,
    MediaStorageDisabledError,
    MediaStorageNotImplementedError,
    get_media_storage_adapter,
)


class MediaStorageAdapterTests(unittest.TestCase):
    def test_disabled_put_raises(self) -> None:
        ad = DisabledMediaStorageAdapter()
        with self.assertRaises(MediaStorageDisabledError):
            ad.put_object(object_key="k", content_type="image/jpeg", body=b"x", metadata={})

    def test_disabled_object_exists_false(self) -> None:
        ad = DisabledMediaStorageAdapter()
        self.assertFalse(ad.object_exists(object_key="any"))

    def test_memory_put_get_roundtrip(self) -> None:
        ad = InMemoryMediaStorageAdapter()
        obj = ad.put_object(
            object_key="offers/1/cover.jpg",
            content_type="image/jpeg",
            body=b"bytes",
            metadata={"a": "b"},
        )
        self.assertEqual(obj.byte_size, 5)
        self.assertTrue(ad.object_exists(object_key="offers/1/cover.jpg"))
        self.assertIsNone(ad.public_url_for(object_key="offers/1/cover.jpg"))

    def test_memory_public_url_when_base_set(self) -> None:
        ad = InMemoryMediaStorageAdapter(public_base_url="https://cdn.example.com/assets")
        ad.put_object(object_key="k", content_type="image/jpeg", body=b"x", metadata={})
        self.assertEqual(ad.public_url_for(object_key="k"), "https://cdn.example.com/assets/k")

    def test_factory_disabled_by_default(self) -> None:
        s = Settings.model_validate(
            {
                "DATABASE_URL": "postgresql+psycopg://x:x@localhost:5432/x",
                "MEDIA_STORAGE_BACKEND": "disabled",
            }
        )
        ad = get_media_storage_adapter(s)
        self.assertIsInstance(ad, DisabledMediaStorageAdapter)

    def test_factory_memory(self) -> None:
        s = Settings.model_validate(
            {
                "DATABASE_URL": "postgresql+psycopg://x:x@localhost:5432/x",
                "MEDIA_STORAGE_BACKEND": "memory",
            }
        )
        ad = get_media_storage_adapter(s)
        self.assertIsInstance(ad, InMemoryMediaStorageAdapter)

    def test_factory_s3_raises_not_implemented(self) -> None:
        s = Settings.model_validate(
            {
                "DATABASE_URL": "postgresql+psycopg://x:x@localhost:5432/x",
                "MEDIA_STORAGE_BACKEND": "s3_compatible",
            }
        )
        with self.assertRaises(MediaStorageNotImplementedError):
            get_media_storage_adapter(s)

    def test_unknown_backend_string_coerces_to_disabled(self) -> None:
        s = Settings.model_validate(
            {
                "DATABASE_URL": "postgresql+psycopg://x:x@localhost:5432/x",
                "MEDIA_STORAGE_BACKEND": "garbage",
            }
        )
        self.assertEqual(s.media_storage_backend, MediaStorageBackend.DISABLED.value)
        ad = get_media_storage_adapter(s)
        self.assertIsInstance(ad, DisabledMediaStorageAdapter)
