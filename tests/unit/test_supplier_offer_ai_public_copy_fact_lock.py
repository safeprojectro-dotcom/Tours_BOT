"""AI public copy fact-lock: snapshot hash + claim validation (no AI HTTP)."""

from __future__ import annotations

from decimal import Decimal

from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus
from app.services.supplier_offer_ai_public_copy_fact_lock import evaluate_ai_public_copy_fact_lock
from app.services.supplier_offer_review_package_service import SupplierOfferReviewPackageService
from app.services.supplier_offer_source_facts_snapshot import (
    build_source_facts_snapshot_v1,
    compute_facts_content_hash,
)
from tests.unit.base import FoundationDBTestCase


class AiPublicCopyFactLockTests(FoundationDBTestCase):
    def test_fact_lock_passes_when_no_ai_block(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        offer.packaging_draft_json = None
        self.session.commit()

        r = evaluate_ai_public_copy_fact_lock(offer)
        self.assertFalse(r.ai_block_present)
        self.assertTrue(r.fact_lock_passed)
        self.assertFalse(r.snapshot_stale)
        self.assertEqual(len(r.blocking_issues), 0)

    def test_fact_lock_passes_when_claims_match_snapshot(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        snap = build_source_facts_snapshot_v1(offer)
        facts = dict(snap.facts)
        offer.packaging_draft_json = {
            "ai_public_copy_v1": {
                "snapshot_ref": snap.content_hash,
                "fact_claims": {
                    "base_price": facts["base_price"],
                    "currency": facts["currency"],
                    "seats_total": facts["seats_total"],
                    "sales_mode": facts["sales_mode"],
                },
            },
        }
        self.session.commit()
        self.session.refresh(offer)

        r = evaluate_ai_public_copy_fact_lock(offer)
        self.assertTrue(r.fact_claims_present)
        self.assertTrue(r.fact_lock_passed)
        self.assertFalse(r.snapshot_stale)

    def test_fact_lock_detects_price_mismatch(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        snap = build_source_facts_snapshot_v1(offer)
        offer.packaging_draft_json = {
            "ai_public_copy_v1": {
                "snapshot_ref": snap.content_hash,
                "fact_claims": {"base_price": "999.99"},
            },
        }
        self.session.commit()
        self.session.refresh(offer)

        r = evaluate_ai_public_copy_fact_lock(offer)
        self.assertTrue(r.fact_claims_present)
        self.assertFalse(r.fact_lock_passed)
        self.assertTrue(any(x.startswith("fact_mismatch:base_price") for x in r.blocking_issues))

    def test_fact_lock_detects_stale_snapshot_ref(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        snap = build_source_facts_snapshot_v1(offer)
        offer.base_price = Decimal("55.00")
        offer.currency = "EUR"
        self.session.flush()

        offer.packaging_draft_json = {
            "ai_public_copy_v1": {
                "snapshot_ref": snap.content_hash,
                "fact_claims": {"base_price": "55.00", "currency": "EUR"},
            },
        }
        self.session.commit()
        self.session.refresh(offer)

        r = evaluate_ai_public_copy_fact_lock(offer)
        self.assertTrue(r.snapshot_stale)
        self.assertFalse(r.fact_lock_passed)
        self.assertTrue(any("snapshot_stale" in x for x in r.blocking_issues))

    def test_fact_lock_unknown_claim_key_blocks(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        snap = build_source_facts_snapshot_v1(offer)
        offer.packaging_draft_json = {
            "ai_public_copy_v1": {
                "snapshot_ref": snap.content_hash,
                "fact_claims": {"made_up_price": "120.00"},
            },
        }
        self.session.commit()
        self.session.refresh(offer)

        r = evaluate_ai_public_copy_fact_lock(offer)
        self.assertFalse(r.fact_lock_passed)
        self.assertTrue(any(x.startswith("unknown_fact_claim_key:") for x in r.blocking_issues))

    def test_snapshot_hash_stable_for_same_facts(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        f1 = build_source_facts_snapshot_v1(offer).facts
        f2 = build_source_facts_snapshot_v1(offer).facts
        self.assertEqual(compute_facts_content_hash(f1), compute_facts_content_hash(f2))

    def test_review_package_includes_ai_public_copy_review(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(
            supplier,
            lifecycle_status=SupplierOfferLifecycle.DRAFT,
            packaging_status=SupplierOfferPackagingStatus.NONE,
        )
        snap = build_source_facts_snapshot_v1(offer)
        offer.packaging_draft_json = {
            "ai_public_copy_v1": {
                "snapshot_ref": snap.content_hash,
                "fact_claims": {"base_price": "999.00"},
            },
        }
        self.session.commit()

        svc = SupplierOfferReviewPackageService()
        pkg = svc.review_package(self.session, offer_id=offer.id)
        self.assertFalse(pkg.ai_public_copy_review.fact_lock_passed)
        self.assertIn("resolve_ai_public_copy_fact_lock", pkg.recommended_next_actions)
        self.assertTrue(any("AI fact lock:" in w for w in pkg.warnings))
