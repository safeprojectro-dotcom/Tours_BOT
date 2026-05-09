"""B7.4C: media ingestion eligibility (B7.4B §4, pure)."""

from __future__ import annotations

import unittest

from app.models.enums import SupplierOfferMediaReviewStatus
from app.services.supplier_offer_media_review_service import MEDIA_REVIEW_KEY
from app.services.supplier_offer_media_ingestion_eligibility import (
    classify_cover_media_reference,
    evaluate_media_ingestion_eligibility,
)
from app.core.media_storage_types import MediaSourceKind
from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX


def _mr(status: str, snap: str) -> dict:
    return {MEDIA_REVIEW_KEY: {"status": status, "cover_media_reference": snap}}


class ClassifySourceTests(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(classify_cover_media_reference(None), MediaSourceKind.EMPTY)
        self.assertEqual(classify_cover_media_reference("  "), MediaSourceKind.EMPTY)

    def test_telegram_photo(self) -> None:
        self.assertEqual(
            classify_cover_media_reference(f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}AbC"),
            MediaSourceKind.TELEGRAM_PHOTO,
        )

    def test_telegram_photo_empty_file_id(self) -> None:
        self.assertEqual(
            classify_cover_media_reference(f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}  "),
            MediaSourceKind.UNSUPPORTED,
        )

    def test_https(self) -> None:
        self.assertEqual(
            classify_cover_media_reference("https://example.com/a.jpg"),
            MediaSourceKind.HTTPS_URL,
        )

    def test_http(self) -> None:
        self.assertEqual(
            classify_cover_media_reference("http://example.com/a.jpg"),
            MediaSourceKind.HTTP_URL,
        )

    def test_unsupported(self) -> None:
        self.assertEqual(classify_cover_media_reference("s3://x"), MediaSourceKind.UNSUPPORTED)


class EligibilityTests(unittest.TestCase):
    def test_allowed_telegram_when_approved_and_aligned(self) -> None:
        ref = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}file1"
        d = _mr(SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value, ref)
        r = evaluate_media_ingestion_eligibility(
            cover_media_reference=ref,
            packaging_draft_json=d,
            allow_https_source=False,
        )
        self.assertTrue(r.allowed)
        self.assertEqual(r.block_codes, ())

    def test_blocked_no_cover(self) -> None:
        r = evaluate_media_ingestion_eligibility(
            cover_media_reference=None,
            packaging_draft_json=_mr(SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value, "x"),
            allow_https_source=False,
        )
        self.assertFalse(r.allowed)
        self.assertIn("ingestion_no_cover_reference", r.block_codes)

    def test_blocked_not_approved(self) -> None:
        ref = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}f"
        r = evaluate_media_ingestion_eligibility(
            cover_media_reference=ref,
            packaging_draft_json=_mr(SupplierOfferMediaReviewStatus.REPLACEMENT_REQUESTED.value, ref),
            allow_https_source=False,
        )
        self.assertFalse(r.allowed)
        self.assertIn("ingestion_not_approved_for_card", r.block_codes)

    def test_blocked_snapshot_mismatch(self) -> None:
        ref = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}new"
        r = evaluate_media_ingestion_eligibility(
            cover_media_reference=ref,
            packaging_draft_json=_mr(
                SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value,
                f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}old",
            ),
            allow_https_source=False,
        )
        self.assertFalse(r.allowed)
        self.assertIn("ingestion_cover_snapshot_mismatch", r.block_codes)

    def test_blocked_http(self) -> None:
        ref = "http://example.com/a.jpg"
        r = evaluate_media_ingestion_eligibility(
            cover_media_reference=ref,
            packaging_draft_json=_mr(SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value, ref),
            allow_https_source=True,
        )
        self.assertFalse(r.allowed)
        self.assertIn("ingestion_http_source_blocked", r.block_codes)

    def test_blocked_https_when_policy_off(self) -> None:
        ref = "https://example.com/a.jpg"
        r = evaluate_media_ingestion_eligibility(
            cover_media_reference=ref,
            packaging_draft_json=_mr(SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value, ref),
            allow_https_source=False,
        )
        self.assertFalse(r.allowed)
        self.assertIn("ingestion_https_source_disabled_by_policy", r.block_codes)

    def test_allowed_https_when_policy_on(self) -> None:
        ref = "https://example.com/a.jpg"
        r = evaluate_media_ingestion_eligibility(
            cover_media_reference=ref,
            packaging_draft_json=_mr(SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value, ref),
            allow_https_source=True,
        )
        self.assertTrue(r.allowed)

    def test_missing_media_review(self) -> None:
        ref = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}f"
        r = evaluate_media_ingestion_eligibility(
            cover_media_reference=ref,
            packaging_draft_json={},
            allow_https_source=False,
        )
        self.assertFalse(r.allowed)
        self.assertIn("ingestion_media_review_missing", r.block_codes)
