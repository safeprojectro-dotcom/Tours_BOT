"""B7.4D: ``publish_safe`` vNext merge helpers."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.core.media_storage_types import StoredObject
from app.models.enums import SupplierOfferMediaReviewStatus
from app.services.supplier_offer_publish_safe_stub import PUBLISH_SAFE_KEY
from app.services.supplier_offer_media_review_service import MEDIA_REVIEW_KEY
from app.services.supplier_offer_publish_safe_vnext import (
    B7_4D_VERSION,
    PublishSafeVNextStatus,
    build_publish_safe_blocked,
    build_publish_safe_deferred,
    build_publish_safe_failed,
    build_publish_safe_pending,
    build_publish_safe_ready,
    fingerprint_source_media_reference,
    mark_publish_safe_ready,
    merge_deferred_publish_safe_compat,
    merge_publish_safe_vnext_into_packaging_draft,
    publish_safe_apply_hero_drift_block,
    review_snapshot_to_stored_value,
)


class FingerprintTests(unittest.TestCase):
    def test_fingerprint_stable(self) -> None:
        a = fingerprint_source_media_reference("telegram_photo:abc")
        b = fingerprint_source_media_reference("telegram_photo:abc")
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_fingerprint_trims(self) -> None:
        self.assertEqual(
            fingerprint_source_media_reference("  telegram_photo:x  "),
            fingerprint_source_media_reference("telegram_photo:x"),
        )


class MergeDraftTests(unittest.TestCase):
    def test_preserves_other_keys(self) -> None:
        draft = {
            "media_review": {"status": "approved_for_card"},
            "card_render_preview": {"x": 1},
            PUBLISH_SAFE_KEY: {"old": True},
        }
        block = build_publish_safe_pending(
            source_media_reference="telegram_photo:z",
            review_snapshot="telegram_photo:z",
            attempt_count=1,
            ingested_by="test",
        )
        out = merge_publish_safe_vnext_into_packaging_draft(draft, block)
        self.assertIs(out["media_review"], draft["media_review"])
        self.assertEqual(out["card_render_preview"], {"x": 1})
        self.assertEqual(out[PUBLISH_SAFE_KEY]["status"], PublishSafeVNextStatus.PENDING.value)


class MarkReadyTests(unittest.TestCase):
    def test_mark_publish_safe_ready_merges(self) -> None:
        offer = SimpleNamespace(
            cover_media_reference="telegram_photo:f",
            packaging_draft_json={
                MEDIA_REVIEW_KEY: {
                    "status": SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value,
                    "cover_media_reference": "telegram_photo:f",
                },
                PUBLISH_SAFE_KEY: {"attempt_count": 2},
            },
        )
        so = StoredObject(
            object_key="supplier-offers/9/cover.bin",
            content_type="image/jpeg",
            byte_size=42,
            etag="e",
            metadata={},
        )
        out = mark_publish_safe_ready(
            offer,
            stored_object=so,
            source_media_reference="telegram_photo:f",
            review_snapshot="telegram_photo:f",
            ingested_by="svc:test",
            storage_kind="memory",
            public_url="https://cdn.example/x",
        )
        ps = out[PUBLISH_SAFE_KEY]
        self.assertEqual(ps["version"], B7_4D_VERSION)
        self.assertEqual(ps["status"], PublishSafeVNextStatus.READY.value)
        self.assertEqual(ps["object_key"], "supplier-offers/9/cover.bin")
        self.assertEqual(ps["attempt_count"], 3)
        self.assertEqual(ps["public_url"], "https://cdn.example/x")


class DriftTests(unittest.TestCase):
    def test_ready_unblocked_when_aligned(self) -> None:
        offer = SimpleNamespace(cover_media_reference="telegram_photo:same", packaging_draft_json=None)
        draft = {
            MEDIA_REVIEW_KEY: {
                "cover_media_reference": "telegram_photo:same",
            },
            PUBLISH_SAFE_KEY: {
                "status": PublishSafeVNextStatus.READY.value,
                "review_snapshot": "telegram_photo:same",
                "object_key": "k",
            },
        }
        out = publish_safe_apply_hero_drift_block(offer, draft, marked_by="admin")
        self.assertEqual(out[PUBLISH_SAFE_KEY]["status"], PublishSafeVNextStatus.READY.value)

    def test_ready_blocked_when_cover_changes(self) -> None:
        offer = SimpleNamespace(cover_media_reference="telegram_photo:new", packaging_draft_json=None)
        draft = {
            MEDIA_REVIEW_KEY: {
                "cover_media_reference": "telegram_photo:new",
            },
            PUBLISH_SAFE_KEY: {
                "status": PublishSafeVNextStatus.READY.value,
                "review_snapshot": "telegram_photo:old",
                "object_key": "k",
                "attempt_count": 3,
            },
        }
        out = publish_safe_apply_hero_drift_block(offer, draft, marked_by="admin")
        ps = out[PUBLISH_SAFE_KEY]
        self.assertEqual(ps["status"], PublishSafeVNextStatus.BLOCKED.value)
        self.assertIsNone(ps["object_key"])
        self.assertEqual(ps["last_error_code"], "publish_safe_hero_drift")


class DeferredCompatTests(unittest.TestCase):
    def test_merge_deferred_vnext_shape(self) -> None:
        offer = SimpleNamespace(cover_media_reference="telegram_photo:c")
        draft = {
            MEDIA_REVIEW_KEY: {
                "cover_media_reference": "telegram_photo:c",
                "status": SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value,
            }
        }
        out = merge_deferred_publish_safe_compat(
            offer, draft, marked_by="m", use_vnext_shape=True
        )
        ps = out[PUBLISH_SAFE_KEY]
        self.assertEqual(ps["version"], B7_4D_VERSION)
        self.assertEqual(ps["status"], PublishSafeVNextStatus.DEFERRED.value)
        self.assertIn("expected_future_storage", ps)


class StateShapeTests(unittest.TestCase):
    def test_failed_has_errors(self) -> None:
        b = build_publish_safe_failed(
            source_media_reference="telegram_photo:x",
            review_snapshot="telegram_photo:x",
            last_error_code="e1",
            last_error_message="msg",
            attempt_count=4,
            ingested_by="junit",
        )
        self.assertEqual(b["status"], PublishSafeVNextStatus.FAILED.value)
        self.assertEqual(b["last_error_code"], "e1")

    def test_blocked_clears_object_fields(self) -> None:
        b = build_publish_safe_blocked(
            reason="policy",
            source_media_reference="telegram_photo:x",
            review_snapshot="telegram_photo:x",
            marked_by="a",
            previous_block={"attempt_count": 5, "storage_kind": "memory"},
        )
        self.assertIsNone(b["object_key"])
        self.assertEqual(b["attempt_count"], 5)


class ReviewSnapshotTests(unittest.TestCase):
    def test_dict_snapshot_sorted_json(self) -> None:
        s = review_snapshot_to_stored_value({"b": 2, "a": 1})
        self.assertEqual(s, '{"a": 1, "b": 2}')
