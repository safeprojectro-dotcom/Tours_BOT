"""B6: branded Telegram preview — deterministic JSON, no publish, no Tour."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import event, select, func

from app.bot.constants import SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX
from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferPackagingStatus,
    SupplierOfferPaymentMode,
    TourSalesMode,
)
from app.models.order import Order
from app.models.supplier import SupplierOffer
from app.models.tour import Tour
from tests.unit.base import FoundationDBTestCase


class B6BrandedPreviewTests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-b6"
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

    def test_get_review_telegram_cover_full_bus_card_lines(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 10, 1, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(days=2)
        o = self.create_supplier_offer(
            s,
            title="Excursie Delta",
            description="Line1 ruta A → B",
            program_text="Ziua 1",
            departure_datetime=dep,
            return_datetime=ret,
            sales_mode=TourSalesMode.FULL_BUS,
            payment_mode=SupplierOfferPaymentMode.ASSISTED_CLOSURE,
            seats_total=50,
            base_price=Decimal("1800.00"),
            currency="RON",
        )
        o.cover_media_reference = f"{SUPPLIER_OFFER_COVER_TELEGRAM_PHOTO_PREFIX}AgACAgI"
        o.packaging_draft_json = {
            "telegram_post_draft": "Caption curat B4, fara stoc live.",
        }
        o.packaging_status = SupplierOfferPackagingStatus.PACKAGING_GENERATED
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b6"}
        r = self.client.get(f"/admin/supplier-offers/{o.id}/packaging/review", headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        d = (r.json().get("packaging_draft_json") or {}) if isinstance(
            r.json().get("packaging_draft_json"), dict
        ) else {}
        p = d.get("branded_telegram_preview") or {}
        self.assertEqual(p.get("template_version"), "b6_v1")
        self.assertEqual(p.get("channel"), "telegram")
        self.assertEqual(p.get("title"), "Excursie Delta")
        c = p.get("cover") or {}
        self.assertEqual(c.get("source"), "telegram_photo")
        self.assertEqual(c.get("status"), "needs_admin_visual_review")
        self.assertTrue(any("tot autobuzul" in str(x.get("value", "")) for x in (p.get("card_lines") or [])))
        self.assertIn("b6_cover_telegram_not_public", str(p.get("warnings") or []))
        self.assertEqual(p.get("caption"), "Caption curat B4, fara stoc live.")

    def test_missing_cover_fallback_and_warning(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 10, 5, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(days=1)
        o = self.create_supplier_offer(
            s,
            title="Fara cover",
            description="D",
            program_text="P",
            departure_datetime=dep,
            return_datetime=ret,
        )
        o.cover_media_reference = None
        o.packaging_draft_json = {"telegram_post_draft": "T"}
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b6"}
        r = self.client.get(f"/admin/supplier-offers/{o.id}/packaging/review", headers=h)
        p = (r.json().get("packaging_draft_json") or {}).get("branded_telegram_preview") or {}
        self.assertTrue(p.get("fallback_branded_card_needed") is True)
        self.assertNotIn("cover", p)
        self.assertIn("b6_cover_missing", str(p.get("warnings") or []))

    def test_per_seat_price_and_no_fake_availability(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 11, 1, 8, 0, tzinfo=UTC)
        ret = dep + timedelta(hours=12)
        o = self.create_supplier_offer(
            s,
            title="Per loc",
            description="Ruta",
            program_text="Prg",
            departure_datetime=dep,
            return_datetime=ret,
            sales_mode=TourSalesMode.PER_SEAT,
            base_price=Decimal("99.50"),
            currency="EUR",
            cover_media_reference="https://example.com/hero.jpg",
        )
        o.packaging_draft_json = {"telegram_post_draft": "OK"}
        self.session.commit()
        h = {"Authorization": "Bearer test-admin-b6"}
        r = self.client.get(f"/admin/supplier-offers/{o.id}/packaging/review", headers=h)
        p = (r.json().get("packaging_draft_json") or {}).get("branded_telegram_preview") or {}
        cl = p.get("card_lines") or []
        joined = " ".join(str(x.get("value", "")) for x in cl)
        self.assertIn("/ persoana", joined)
        self.assertIn("Locurile se confirma la rezervare", joined)
        self.assertNotIn("b6_cover_telegram_not_public", str(p.get("warnings") or []))
        c = p.get("cover") or {}
        self.assertEqual(c.get("source"), "url")
        for line in cl:
            self.assertNotRegex(
                str(line.get("value", "")),
                r"(?i)ultim|last\s+seats|selling\s+fast|only\s+\d+\s+left",
            )

    def test_post_persist_in_db(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 12, 1, 7, 0, tzinfo=UTC)
        ret = dep + timedelta(days=1)
        o = self.create_supplier_offer(
            s,
            title="Persist",
            description="D",
            program_text="P",
            departure_datetime=dep,
            return_datetime=ret,
        )
        o.packaging_draft_json = {"telegram_post_draft": "X", "source": "deterministic"}
        self.session.commit()
        oid = o.id
        h = {"Authorization": "Bearer test-admin-b6"}
        r = self.client.post(
            f"/admin/supplier-offers/{oid}/packaging/branded-preview/generate",
            headers=h,
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.session.expire_all()
        row = self.session.get(SupplierOffer, oid)
        assert row is not None
        d = row.packaging_draft_json or {}
        self.assertIn("branded_telegram_preview", d)
        self.assertIn("b6_v1", str(d.get("branded_telegram_preview", {}).get("template_version", "")))
        self.assertEqual(d.get("source"), "deterministic")
        self.assertEqual(d.get("telegram_post_draft"), "X")

    def test_no_lifecycle_or_publish_side_effects(self) -> None:
        s = self.create_supplier()
        dep = datetime(2026, 5, 1, 6, 0, tzinfo=UTC)
        ret = dep + timedelta(days=1)
        o = self.create_supplier_offer(
            s,
            title="Side",
            description="D",
            program_text="P",
            departure_datetime=dep,
            return_datetime=ret,
            lifecycle_status=SupplierOfferLifecycle.READY_FOR_MODERATION,
        )
        o.published_at = None
        o.showcase_message_id = None
        o.showcase_chat_id = None
        o.packaging_draft_json = {"telegram_post_draft": "T"}
        self.session.commit()
        oid = o.id
        n_tour = self.session.scalar(select(func.count()).select_from(Tour)) or 0
        n_order = self.session.scalar(select(func.count()).select_from(Order)) or 0
        h = {"Authorization": "Bearer test-admin-b6"}
        r1 = self.client.get(f"/admin/supplier-offers/{oid}/packaging/review", headers=h)
        r2 = self.client.post(
            f"/admin/supplier-offers/{oid}/packaging/branded-preview/generate",
            headers=h,
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200, r2.text)
        self.session.expire_all()
        row = self.session.get(SupplierOffer, oid)
        assert row is not None
        self.assertEqual(row.lifecycle_status, SupplierOfferLifecycle.READY_FOR_MODERATION)
        self.assertIsNone(row.published_at)
        self.assertIsNone(row.showcase_message_id)
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Tour)), n_tour)
        self.assertEqual(self.session.scalar(select(func.count()).select_from(Order)), n_order)
