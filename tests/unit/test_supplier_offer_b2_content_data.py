"""B2: supplier_offer extended fields persist and surface on supplier-admin + admin APIs."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOfferPackagingStatus
from app.models.supplier import SupplierOffer
from tests.unit.base import FoundationDBTestCase


class SupplierOfferB2ContentDataTests(FoundationDBTestCase):
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
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        get_settings().admin_api_token = self._original_admin
        self.client.close()
        self.app.dependency_overrides.clear()
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_create_and_read_b2_fields_supplier_and_admin(self) -> None:
        admin_headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            "/admin/suppliers",
            headers=admin_headers,
            json={"code": "B2-1", "display_name": "B2 Co", "credential_label": "t"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        token = r.json()["api_token"]

        dep = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 9, 1, 20, 0, tzinfo=UTC)
        vf = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
        vu = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
        payload = {
            "title": "B2 trip",
            "description": "Desc",
            "program_text": "Program",
            "departure_datetime": dep.isoformat(),
            "return_datetime": ret.isoformat(),
            "vehicle_label": "V",
            "seats_total": 20,
            "base_price": "100.00",
            "currency": "EUR",
            "cover_media_reference": "s3://bucket/hero",
            "media_references": [{"id": "a", "url": "https://example.com/x.jpg"}],
            "included_text": "Transport",
            "excluded_text": "Meals",
            "short_hook": "One line",
            "marketing_summary": "Longer marketing",
            "discount_code": "EARLY",
            "discount_percent": "10.5",
            "discount_amount": "5.00",
            "discount_valid_until": "2026-10-01T00:00:00+00:00",
            "recurrence_type": "rrule",
            "recurrence_rule": "FREQ=WEEKLY;BYDAY=SA",
            "valid_from": vf.isoformat(),
            "valid_until": vu.isoformat(),
            "supplier_admin_notes": "Supplier note",
        }
        c = self.client.post("/supplier-admin/offers", headers={"Authorization": f"Bearer {token}"}, json=payload)
        self.assertEqual(c.status_code, 201, c.text)
        body = c.json()
        self.assertEqual(body["cover_media_reference"], "s3://bucket/hero")
        self.assertEqual(body["media_references"], [{"id": "a", "url": "https://example.com/x.jpg"}])
        self.assertEqual(body["included_text"], "Transport")
        self.assertEqual(body["discount_percent"], "10.50")
        self.assertNotIn("packaging_status", body)
        self.assertNotIn("admin_internal_notes", body)

        oid = body["id"]
        admin = self.client.get(f"/admin/supplier-offers/{oid}", headers=admin_headers)
        self.assertEqual(admin.status_code, 200, admin.text)
        ad = admin.json()
        self.assertEqual(ad["packaging_status"], "none")
        self.assertIsNone(ad["admin_internal_notes"])
        self.assertIsNone(ad["quality_warnings_json"])
        self.assertIsNone(ad["missing_fields_json"])

    def test_model_roundtrip_packaging_status(self) -> None:
        s = self.create_supplier()
        o = self.create_supplier_offer(s)
        o.packaging_status = SupplierOfferPackagingStatus.PACKAGING_GENERATED
        o.admin_internal_notes = "ops"
        o.quality_warnings_json = ["weak_title"]
        o.missing_fields_json = {"hero": True}
        self.session.flush()
        self.session.expire_all()
        row = self.session.get(SupplierOffer, o.id)
        assert row is not None
        self.assertEqual(row.packaging_status, SupplierOfferPackagingStatus.PACKAGING_GENERATED)
        self.assertEqual(row.admin_internal_notes, "ops")
        self.assertEqual(row.quality_warnings_json, ["weak_title"])
        self.assertEqual(row.missing_fields_json, {"hero": True})

    def test_discount_validators_reject(self) -> None:
        admin_headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            "/admin/suppliers", headers=admin_headers, json={"code": "B2-2", "display_name": "X", "credential_label": "t"}
        )
        self.assertEqual(r.status_code, 201)
        token = r.json()["api_token"]
        dep = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 9, 1, 20, 0, tzinfo=UTC)
        bad = self.client.post(
            "/supplier-admin/offers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "T",
                "description": "D",
                "departure_datetime": dep.isoformat(),
                "return_datetime": ret.isoformat(),
                "vehicle_label": "V",
                "seats_total": 1,
                "base_price": "1",
                "currency": "EUR",
                "discount_percent": "101",
            },
        )
        self.assertEqual(bad.status_code, 422)

    def test_update_valid_window(self) -> None:
        admin_headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            "/admin/suppliers", headers=admin_headers, json={"code": "B2-3", "display_name": "Y", "credential_label": "t"}
        )
        self.assertEqual(r.status_code, 201)
        token = r.json()["api_token"]
        dep = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 9, 1, 20, 0, tzinfo=UTC)
        c = self.client.post(
            "/supplier-admin/offers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "T",
                "description": "D",
                "departure_datetime": dep.isoformat(),
                "return_datetime": ret.isoformat(),
                "vehicle_label": "V",
                "seats_total": 1,
                "base_price": "1",
                "currency": "EUR",
            },
        )
        self.assertEqual(c.status_code, 201)
        oid = c.json()["id"]
        u = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "valid_from": "2026-10-01T00:00:00+00:00",
                "valid_until": "2026-01-01T00:00:00+00:00",
            },
        )
        self.assertEqual(u.status_code, 422)
