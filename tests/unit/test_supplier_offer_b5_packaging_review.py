"""B5: admin packaging review API — no publish, no lifecycle change, no Tour."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, select, func
from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOfferLifecycle, SupplierOfferPackagingStatus, SupplierOfferPaymentMode, TourSalesMode
from app.models.order import Order
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from tests.unit.base import FoundationDBTestCase


class B5PackagingReviewAPITests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.nested = self.connection.begin_nested()

        @event.listens_for(self.session, "after_transaction_end")
        def restart_savepoint(session, transaction) -> None:
            parent = getattr(transaction, "_parent", None)
            if transaction.nested and not getattr(parent, "nested", False):
                self.nested = self.connection.begin_nested()

        self._restart_savepoint = restart_savepoint
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-b5"
        self.app.dependency_overrides[get_db] = self._db_override
        self.client = TestClient(self.app)

    def _db_override(self):
        yield self.session

    def tearDown(self) -> None:
        get_settings().admin_api_token = self._original_admin
        self.client.close()
        self.app.dependency_overrides.clear()
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def _offer_with_packaging(self, *, packaging_status: SupplierOfferPackagingStatus) -> SupplierOffer:
        s = self.create_supplier()
        dep = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        ret = dep + timedelta(days=1)
        o = self.create_supplier_offer(
            s,
            title="B5 Offer",
            description="Line1 route\n\nMore body text",
            program_text="Day program",
            departure_datetime=dep,
            return_datetime=ret,
            seats_total=40,
            base_price=Decimal("100.00"),
            currency="EUR",
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION,
            packaging_status=packaging_status,
        )
        o.packaging_draft_json = {
            "telegram_post_draft": "ORIGINAL_TG",
            "source": "deterministic",
        }
        o.missing_fields_json = {"field_codes": [], "b4": True}
        o.quality_warnings_json = {"items": [], "b4": True}
        self.session.flush()
        return o

    def test_get_review_returns_draft_and_packaging_fields(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.PACKAGING_GENERATED)
        self.session.commit()
        oid = o.id
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.get(f"/admin/supplier-offers/{oid}/packaging/review", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["title"], "B5 Offer")
        self.assertEqual((j.get("packaging_draft_json") or {}).get("telegram_post_draft"), "ORIGINAL_TG")
        self.assertIn("packaging_status", j)

    def test_approve_from_generated(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.PACKAGING_GENERATED)
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/packaging/approve",
            headers=h,
            json={"accept_warnings": False, "reviewed_by": "admin@test"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["packaging_status"], "approved_for_publish")
        self.assertEqual(j.get("packaging_reviewed_by"), "admin@test")
        self.assertIsNotNone(j.get("packaging_reviewed_at"))

    def test_approve_needs_review_without_accept_fails(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.NEEDS_ADMIN_REVIEW)
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/packaging/approve",
            headers=h,
            json={"accept_warnings": False},
        )
        self.assertEqual(r.status_code, 400, r.text)

    def test_approve_needs_review_with_accept_works(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.NEEDS_ADMIN_REVIEW)
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/packaging/approve",
            headers=h,
            json={"accept_warnings": True},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["packaging_status"], "approved_for_publish")

    def test_reject_stores_reason_and_status(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.PACKAGING_GENERATED)
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/packaging/reject",
            headers=h,
            json={"reason": "  Bad copy  ", "reviewed_by": "r1"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["packaging_status"], "packaging_rejected")
        self.assertEqual(j.get("packaging_rejection_reason"), "Bad copy")

    def test_request_clarification(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.PACKAGING_GENERATED)
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/packaging/request-clarification",
            headers=h,
            json={"reason": "Need price clarity"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(j["packaging_status"], "clarification_requested")
        self.assertEqual(j.get("clarification_reason"), "Need price clarity")

    def test_patch_draft_updates_telegram_only(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.PACKAGING_GENERATED)
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.patch(
            f"/admin/supplier-offers/{o.id}/packaging/draft",
            headers=h,
            json={"telegram_post_draft": "EDITED_POST"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        d = (r.json().get("packaging_draft_json") or {}) if isinstance(r.json().get("packaging_draft_json"), dict) else {}
        self.assertEqual(d.get("telegram_post_draft"), "EDITED_POST")
        self.assertEqual(d.get("source"), "deterministic")

    def test_patch_draft_fails_after_approve(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.APPROVED_FOR_PUBLISH)
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.patch(
            f"/admin/supplier-offers/{o.id}/packaging/draft",
            headers=h,
            json={"telegram_post_draft": "X"},
        )
        self.assertEqual(r.status_code, 400, r.text)

    def test_no_lifecycle_or_publish_touched(self) -> None:
        o = self._offer_with_packaging(packaging_status=SupplierOfferPackagingStatus.PACKAGING_GENERATED)
        o.published_at = None
        self.session.commit()
        oid = o.id
        n_t = self.session.scalar(select(func.count()).select_from(Tour)) or 0
        n_o = self.session.scalar(select(func.count()).select_from(Order)) or 0
        h = {"Authorization": "Bearer test-admin-b5"}
        r = self.client.post(
            f"/admin/supplier-offers/{oid}/packaging/approve",
            headers=h,
            json={"accept_warnings": True},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.session.expire_all()
        row = self.session.get(SupplierOffer, oid)
        assert row is not None
        self.assertEqual(row.lifecycle_status, SupplierOfferLifecycle.READY_FOR_MODERATION)
        self.assertIsNone(row.published_at)
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Tour)), n_t)
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Order)), n_o)
