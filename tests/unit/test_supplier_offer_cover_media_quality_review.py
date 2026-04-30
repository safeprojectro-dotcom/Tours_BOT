"""C2B5: deterministic cover/showcase media warnings (read-only)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX
from app.models.enums import SupplierOfferMediaReviewStatus
from app.services.supplier_offer_cover_media_quality_review import evaluate_cover_media_quality_review
from app.services.supplier_offer_media_review_service import MEDIA_REVIEW_KEY


def _row(
    *,
    cover: str | None = None,
    showcase_photo_url: str | None = None,
    packaging_draft_json: dict | None = None,
):
    return SimpleNamespace(
        cover_media_reference=cover,
        showcase_photo_url=showcase_photo_url,
        packaging_draft_json=packaging_draft_json,
    )


class CoverMediaQualityReviewTests(unittest.TestCase):
    def test_missing_cover_text_only_warning(self) -> None:
        r = evaluate_cover_media_quality_review(_row(cover=None))
        codes = [w.code for w in r.warnings]
        self.assertIn("cover_media_missing_showcase_photo", codes)
        self.assertTrue(r.has_warnings)

    def test_unsupported_scheme_warning(self) -> None:
        r = evaluate_cover_media_quality_review(_row(cover="s3://bucket/key"))
        codes = [w.code for w in r.warnings]
        self.assertIn("cover_media_not_sendable_for_showcase", codes)
        self.assertNotIn("cover_media_not_explicitly_approved_for_card", codes)

    def test_https_without_media_review_warns_approve(self) -> None:
        r = evaluate_cover_media_quality_review(_row(cover="https://cdn.example/hero.jpg"))
        codes = [w.code for w in r.warnings]
        self.assertIn("cover_media_not_explicitly_approved_for_card", codes)

    def test_telegram_prefix_aligned_approval_no_warnings(self) -> None:
        ref = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}AgACAgIAAxkBAAIB"
        draft = {
            MEDIA_REVIEW_KEY: {
                "status": SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value,
                "cover_media_reference": ref,
            },
        }
        r = evaluate_cover_media_quality_review(_row(cover=ref, packaging_draft_json=draft))
        self.assertFalse(r.has_warnings)
        self.assertEqual(r.warnings, [])

    def test_snapshot_mismatch_warning(self) -> None:
        ref_old = "https://cdn.example/old.jpg"
        ref_new = "https://cdn.example/new.jpg"
        draft = {
            MEDIA_REVIEW_KEY: {
                "status": SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value,
                "cover_media_reference": ref_old,
            },
        }
        r = evaluate_cover_media_quality_review(_row(cover=ref_new, packaging_draft_json=draft))
        codes = [w.code for w in r.warnings]
        self.assertIn("media_review_cover_snapshot_mismatch", codes)
        self.assertNotIn(
            "cover_media_not_explicitly_approved_for_card",
            codes,
            "drift replaces stale approve reminder",
        )

    def test_negative_media_review_suppresses_approve_nudge(self) -> None:
        ref = "https://cdn.example/x.jpg"
        draft = {
            MEDIA_REVIEW_KEY: {
                "status": SupplierOfferMediaReviewStatus.REJECTED_IRRELEVANT.value,
                "cover_media_reference": ref,
                "reason": "wrong scene",
            },
        }
        r = evaluate_cover_media_quality_review(_row(cover=ref, packaging_draft_json=draft))
        codes = [w.code for w in r.warnings]
        self.assertIn("media_review_rejected_irrelevant", codes)
        self.assertNotIn("cover_media_not_explicitly_approved_for_card", codes)

    def test_showcase_photo_url_without_cover(self) -> None:
        r = evaluate_cover_media_quality_review(
            _row(cover=None, showcase_photo_url="https://cdn.example/only_here.jpg"),
        )
        codes = [w.code for w in r.warnings]
        self.assertIn("showcase_photo_url_without_cover_media_reference", codes)

    def test_showcase_photo_url_differs_from_cover(self) -> None:
        r = evaluate_cover_media_quality_review(
            _row(cover="https://cdn.example/a.jpg", showcase_photo_url="https://cdn.example/b.jpg"),
        )
        codes = [w.code for w in r.warnings]
        self.assertIn("showcase_photo_url_differs_from_cover_media_reference", codes)
