"""B7.2: card_render_preview JSON plan — no pixels, no Telegram, no publish."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, select, func

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX
from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOfferLifecycle, TourSalesMode
from app.models.order import Order
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from tests.unit.base import FoundationDBTestCase


class B72CardRenderPreviewTests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-b72"
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

    def test_approved_for_card_render_plan_ready(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 9, 10, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(days=1)
        ref = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}FILE1"
        o = self.create_supplier_offer(
            s,
            title="Card Title",
            description="Ruta A → B\n\nBody",
            program_text="P",
            departure_datetime=dep,
            return_datetime=ret,
            base_price=Decimal("50.00"),
            currency="EUR",
            sales_mode=TourSalesMode.PER_SEAT,
            cover_media_reference=ref,
        )
        o.packaging_draft_json = {
            "telegram_post_draft": "Short caption",
            "media_review": {
                "version": "b7_1",
                "cover_media_reference": ref,
                "status": "approved_for_card",
                "reason": None,
                "reviewed_at": "2026-01-01T00:00:00+00:00",
                "reviewed_by": "a",
            },
        }
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b72"}
        r = self.client.post(f"/admin/supplier-offers/{o.id}/media/card-preview/generate", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        cr = (r.json().get("packaging_draft_json") or {}).get("card_render_preview") or {}
        self.assertEqual(cr.get("version"), "b7_2")
        self.assertEqual(cr.get("status"), "render_plan_ready")
        self.assertEqual((cr.get("source") or {}).get("mode"), "approved_cover")
        self.assertEqual((cr.get("source") or {}).get("cover_media_reference"), ref)
        self.assertEqual((cr.get("layout") or {}).get("aspect_ratio"), "4:5")
        roles = [x.get("role") for x in (cr.get("text_layers") or [])]
        self.assertIn("title", roles)
        self.assertIn("date", roles)
        self.assertIn("price", roles)

    def test_fallback_plan_ready(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 9, 11, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(hours=8)
        o = self.create_supplier_offer(
            s,
            title="FB",
            description="D",
            program_text="P",
            departure_datetime=dep,
            return_datetime=ret,
            cover_media_reference=None,
        )
        o.packaging_draft_json = {
            "media_review": {
                "version": "b7_1",
                "cover_media_reference": None,
                "status": "fallback_card_required",
                "reason": None,
                "reviewed_at": "2026-01-01T00:00:00+00:00",
                "reviewed_by": "b",
            },
        }
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b72"}
        r = self.client.post(f"/admin/supplier-offers/{o.id}/media/card-preview/generate", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        cr = (r.json().get("packaging_draft_json") or {}).get("card_render_preview") or {}
        self.assertEqual(cr.get("status"), "fallback_plan_ready")
        self.assertEqual((cr.get("source") or {}).get("mode"), "fallback_branded_background")
        self.assertEqual((cr.get("source") or {}).get("source_status"), "fallback_card_required")

    def test_no_media_review_blocked(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 9, 12, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(hours=8)
        o = self.create_supplier_offer(
            s,
            title="X",
            description="D line1",
            program_text="P",
            departure_datetime=dep,
            return_datetime=ret,
        )
        o.packaging_draft_json = {"telegram_post_draft": "T"}
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b72"}
        r = self.client.post(f"/admin/supplier-offers/{o.id}/media/card-preview/generate", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        cr = (r.json().get("packaging_draft_json") or {}).get("card_render_preview") or {}
        self.assertEqual(cr.get("status"), "blocked_needs_photo_review")
        w = str(cr.get("warnings") or [])
        self.assertIn("b7_2_needs_photo_review", w)

    def test_text_layers_from_branded_not_row_invention(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 9, 13, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(days=1)
        ref = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}z"
        o = self.create_supplier_offer(
            s,
            title="ExactTitle",
            description="OnlyDesc",
            program_text="",
            departure_datetime=dep,
            return_datetime=ret,
            transport_notes=None,
            cover_media_reference=ref,
        )
        o.packaging_draft_json = {
            "media_review": {
                "status": "approved_for_card",
                "cover_media_reference": ref,
            },
        }
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b72"}
        r = self.client.post(f"/admin/supplier-offers/{o.id}/media/card-preview/generate", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        cr = (r.json().get("packaging_draft_json") or {}).get("card_render_preview") or {}
        tl = {x.get("role"): x.get("text") for x in (cr.get("text_layers") or []) if isinstance(x, dict)}
        self.assertEqual(tl.get("title"), "ExactTitle")
        self.assertNotRegex(tl.get("date") or "", r"\d{4}-\d{2}-\d{2}T")

    def test_no_lifecycle_or_publish_fields(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 9, 14, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(hours=10)
        ref = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}w"
        o = self.create_supplier_offer(
            s,
            title="L",
            description="D",
            program_text="P",
            departure_datetime=dep,
            return_datetime=ret,
            cover_media_reference=ref,
        )
        o.lifecycle_status = SupplierOfferLifecycle.READY_FOR_MODERATION
        o.published_at = None
        o.showcase_message_id = None
        o.showcase_chat_id = None
        o.packaging_draft_json = {"media_review": {"status": "approved_for_card", "cover_media_reference": ref}}
        self.session.commit()
        oid = o.id
        n_tour = self.session.scalar(select(func.count()).select_from(Tour)) or 0
        n_order = self.session.scalar(select(func.count()).select_from(Order)) or 0
        h = {"Authorization": "Bearer test-admin-b72"}
        r = self.client.post(f"/admin/supplier-offers/{oid}/media/card-preview/generate", headers=h)
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
