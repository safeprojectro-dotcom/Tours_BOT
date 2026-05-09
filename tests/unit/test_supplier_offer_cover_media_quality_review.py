"""C2B5: deterministic cover/showcase media warnings (read-only)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX
from app.models.enums import SupplierOfferMediaReviewStatus
from app.schemas.supplier_admin import AdminSupplierOfferCoverMediaQualityReviewRead, CoverMediaWarningItemRead
from app.services.supplier_offer_cover_media_quality_review import (
    TEXT_ONLY_PUBLICATION_MODE,
    approve_cover_for_card_operator_action_disabled_reasons,
    cover_media_publish_blocking_reasons,
    evaluate_cover_media_quality_review,
)
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


class CoverMediaPublishBlockingReasonsTests(unittest.TestCase):
    def test_photo_mode_blocks_on_replacement_requested_warning(self) -> None:
        cm = AdminSupplierOfferCoverMediaQualityReviewRead(
            warnings=[
                CoverMediaWarningItemRead(code="media_review_replacement_requested", message="replace hero."),
            ],
            has_warnings=True,
        )
        dr = cover_media_publish_blocking_reasons(
            cover_media_quality_review=cm,
            publication_mode="photo_with_caption",
        )
        self.assertEqual(len(dr), 1)
        self.assertIn("media_review_replacement_requested", dr[0])

    def test_text_only_ignores_photo_only_codes(self) -> None:
        cm = AdminSupplierOfferCoverMediaQualityReviewRead(
            warnings=[
                CoverMediaWarningItemRead(
                    code="cover_media_not_explicitly_approved_for_card",
                    message="approve card",
                ),
                CoverMediaWarningItemRead(
                    code="cover_media_not_sendable_for_showcase",
                    message="bad scheme",
                ),
            ],
            has_warnings=True,
        )
        dr = cover_media_publish_blocking_reasons(
            cover_media_quality_review=cm,
            publication_mode=TEXT_ONLY_PUBLICATION_MODE,
        )
        self.assertEqual(dr, [])

    def test_never_blocks_cover_media_missing_for_text_only_stack(self) -> None:
        cm = AdminSupplierOfferCoverMediaQualityReviewRead(
            warnings=[
                CoverMediaWarningItemRead(code="cover_media_missing_showcase_photo", message="text-only OK"),
            ],
            has_warnings=True,
        )
        dr = cover_media_publish_blocking_reasons(
            cover_media_quality_review=cm,
            publication_mode=TEXT_ONLY_PUBLICATION_MODE,
        )
        self.assertEqual(dr, [])


class ApproveCoverForCardOperatorActionTests(unittest.TestCase):
    def test_disabled_when_no_cover(self) -> None:
        dr = approve_cover_for_card_operator_action_disabled_reasons(_row(cover=None))
        self.assertTrue(dr)

    def test_disabled_when_not_sendable(self) -> None:
        dr = approve_cover_for_card_operator_action_disabled_reasons(_row(cover="s3://bucket/o"))
        self.assertTrue(dr)

    def test_disabled_when_already_aligned_approved(self) -> None:
        ref = "https://cdn.example/x.jpg"
        draft = {
            MEDIA_REVIEW_KEY: {
                "status": SupplierOfferMediaReviewStatus.APPROVED_FOR_CARD.value,
                "cover_media_reference": ref,
            },
        }
        dr = approve_cover_for_card_operator_action_disabled_reasons(_row(cover=ref, packaging_draft_json=draft))
        self.assertTrue(dr)

    def test_disabled_when_replacement_requested_snapshot_matches_cover(self) -> None:
        ref = "https://cdn.example/x.jpg"
        draft = {
            MEDIA_REVIEW_KEY: {
                "status": SupplierOfferMediaReviewStatus.REPLACEMENT_REQUESTED.value,
                "cover_media_reference": ref,
            },
        }
        dr = approve_cover_for_card_operator_action_disabled_reasons(_row(cover=ref, packaging_draft_json=draft))
        self.assertTrue(dr)
        self.assertTrue(any("replacement" in x.lower() or "unsuitable" in x.lower() for x in dr))

    def test_enabled_when_replacement_requested_snapshot_differs_from_cover(self) -> None:
        cur = "https://cdn.example/new.jpg"
        snap = "https://cdn.example/old.jpg"
        draft = {
            MEDIA_REVIEW_KEY: {
                "status": SupplierOfferMediaReviewStatus.REPLACEMENT_REQUESTED.value,
                "cover_media_reference": snap,
            },
        }
        dr = approve_cover_for_card_operator_action_disabled_reasons(_row(cover=cur, packaging_draft_json=draft))
        self.assertEqual(dr, [])

    def test_disabled_when_rejected_bad_quality_snapshot_matches_cover(self) -> None:
        ref = "https://cdn.example/x.jpg"
        draft = {
            MEDIA_REVIEW_KEY: {
                "status": SupplierOfferMediaReviewStatus.REJECTED_BAD_QUALITY.value,
                "cover_media_reference": ref,
            },
        }
        dr = approve_cover_for_card_operator_action_disabled_reasons(_row(cover=ref, packaging_draft_json=draft))
        self.assertTrue(dr)
