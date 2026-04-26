"""B7.1: admin media review metadata in packaging_draft_json — no getFile, no images, no publish."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, select, func

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX
from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOfferLifecycle
from app.models.order import Order
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from tests.unit.base import FoundationDBTestCase


class B71MediaReviewAPITests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-b71"
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

    def _offer(self, **kw) -> SupplierOffer:
        s = self.create_supplier()
        dep = kw.pop("departure_datetime", datetime(2026, 8, 1, 6, 0, tzinfo=UTC))
        ret = kw.pop("return_datetime", dep + timedelta(days=1))
        return self.create_supplier_offer(
            s,
            title=kw.pop("title", "B7.1 offer"),
            description=kw.pop("description", "Desc"),
            program_text=kw.pop("program_text", "P"),
            departure_datetime=dep,
            return_datetime=ret,
            **kw,
        )

    def test_get_media_review_has_cover_and_metadata(self) -> None:
        o = self._offer(
            cover_media_reference=f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}abc",
        )
        o.packaging_draft_json = {"media_review": {"version": "b7_1", "status": "approved_for_card"}}
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.get(f"/admin/supplier-offers/{o.id}/media/review", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertIn("telegram_photo:abc", j.get("cover_media_reference") or "")
        mr = (j.get("packaging_draft_json") or {}).get("media_review") or {}
        self.assertEqual(mr.get("status"), "approved_for_card")

    def test_approve_stores_approved_for_card(self) -> None:
        o = self._offer(cover_media_reference=f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}x1")
        o.packaging_draft_json = {}
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/media/approve-for-card",
            headers=h,
            json={"reviewed_by": "admin1"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        mr = (r.json().get("packaging_draft_json") or {}).get("media_review") or {}
        self.assertEqual(mr.get("version"), "b7_1")
        self.assertEqual(mr.get("status"), "approved_for_card")
        self.assertIn("telegram_photo", mr.get("cover_media_reference", ""))
        self.assertIsNone(mr.get("reason"))
        self.assertEqual(mr.get("reviewed_by"), "admin1")
        self.assertIsNotNone(mr.get("reviewed_at"))

    def test_approve_without_cover_fails(self) -> None:
        o = self._offer(cover_media_reference=None)
        o.packaging_draft_json = {}
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/media/approve-for-card",
            headers=h,
            json={},
        )
        self.assertEqual(r.status_code, 400, r.text)
        self.assertIn("cover", (r.json().get("detail") or ""))

    def test_reject_requires_reason(self) -> None:
        o = self._offer(cover_media_reference="https://x/y.jpg")
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/media/reject",
            headers=h,
            json={"kind": "bad_quality", "reason": "   "},
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_reject_bad_quality(self) -> None:
        o = self._offer(cover_media_reference="https://x/y.jpg")
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/media/reject",
            headers=h,
            json={"kind": "bad_quality", "reason": "Too blurry", "reviewed_by": "a"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        mr = (r.json().get("packaging_draft_json") or {}).get("media_review") or {}
        self.assertEqual(mr.get("status"), "rejected_bad_quality")
        self.assertEqual(mr.get("reason"), "Too blurry")

    def test_reject_irrelevant(self) -> None:
        o = self._offer(cover_media_reference="https://x/y.jpg")
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/media/reject",
            headers=h,
            json={"kind": "irrelevant", "reason": "Wrong place"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        mr = (r.json().get("packaging_draft_json") or {}).get("media_review") or {}
        self.assertEqual(mr.get("status"), "rejected_irrelevant")

    def test_request_replacement_requires_reason(self) -> None:
        o = self._offer(cover_media_reference="u")
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/media/request-replacement",
            headers=h,
            json={"reason": ""},
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_request_replacement(self) -> None:
        o = self._offer(cover_media_reference="u")
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/media/request-replacement",
            headers=h,
            json={"reason": "Need better angle", "reviewed_by": "r1"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        mr = (r.json().get("packaging_draft_json") or {}).get("media_review") or {}
        self.assertEqual(mr.get("status"), "replacement_requested")
        self.assertEqual(mr.get("reason"), "Need better angle")

    def test_fallback_with_no_cover(self) -> None:
        o = self._offer(cover_media_reference=None)
        o.packaging_draft_json = {}
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{o.id}/media/use-fallback-card",
            headers=h,
            json={},
        )
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertIsNone(j.get("cover_media_reference"))
        mr = (j.get("packaging_draft_json") or {}).get("media_review") or {}
        self.assertEqual(mr.get("status"), "fallback_card_required")
        self.assertIsNone(mr.get("cover_media_reference"))
        self.assertIsNone(mr.get("reason"))

    def test_no_lifecycle_or_publish_touched(self) -> None:
        o = self._offer(
            cover_media_reference=f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}z",
        )
        o.lifecycle_status = SupplierOfferLifecycle.READY_FOR_MODERATION
        o.published_at = None
        o.showcase_message_id = None
        o.showcase_chat_id = None
        self.session.commit()
        oid = o.id
        n_tour = self.session.scalar(select(func.count()).select_from(Tour)) or 0
        n_order = self.session.scalar(select(func.count()).select_from(Order)) or 0
        h = {"Authorization": "Bearer test-admin-b71"}
        r = self.client.post(
            f"/admin/supplier-offers/{oid}/media/approve-for-card",
            headers=h,
            json={"reviewed_by": "x"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.session.expire_all()
        row = self.session.get(SupplierOffer, oid)
        assert row is not None
        self.assertEqual(row.lifecycle_status, SupplierOfferLifecycle.READY_FOR_MODERATION)
        self.assertIsNone(row.published_at)
        self.assertIsNone(row.showcase_message_id)
        self.assertIsNone(row.showcase_chat_id)
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Tour)), n_tour)
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Order)), n_order)
