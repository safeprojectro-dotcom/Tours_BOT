"""B16: GET /admin/ops-dashboard read-only OPS visibility."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import update

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import (
    BookingStatus,
    CancellationStatus,
    PaymentStatus,
    SupplierOfferShowcasePublishAttemptStatus,
    SupplierOfferShowcasePublishActorSurface,
    TourStatus,
)
from app.models.supplier import SupplierOfferExecutionLink
from app.models.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttempt
from tests.unit.base import FoundationDBTestCase


class AdminOpsDashboardTests(FoundationDBTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.app = create_app()
        self._original_admin = get_settings().admin_api_token
        get_settings().admin_api_token = "test-admin-secret"

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        super().tearDown()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-admin-secret"}

    def test_ops_dashboard_401_without_token(self) -> None:
        r = self.client.get("/admin/ops-dashboard")
        self.assertEqual(r.status_code, 401)

    def test_ops_dashboard_shape_read_only(self) -> None:
        r = self.client.get("/admin/ops-dashboard", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertIn("summary", body)
        for k in (
            "upcoming_tours_count",
            "open_for_sale_tours_count",
            "active_holds_count",
            "pending_payment_orders_count",
            "confirmed_orders_count",
            "expired_or_closed_orders_count",
            "open_handoffs_count",
            "attention_items_count",
        ):
            self.assertIn(k, body["summary"])
        self.assertIsInstance(body["attention_items"], list)
        self.assertIsInstance(body["recent_orders"], list)
        self.assertIsInstance(body["upcoming_tours"], list)
        self.assertIsInstance(body["recent_publications"], list)
        self.assertIsInstance(body["conversion_links"], list)
        self.assertIn("generated_at", body)
        self.assertIn("audit_hint", body)
        self.assertIn("Read-only OPS dashboard", body["audit_hint"])
        f = body["filters"]
        self.assertEqual(f["days_ahead"], 30)
        self.assertEqual(f["recent_days"], 7)
        self.assertEqual(f["orders_limit"], 20)
        self.assertEqual(f["tours_limit"], 15)
        self.assertEqual(f["publications_limit"], 20)
        self.assertEqual(f["conversion_links_limit"], 20)
        self.assertEqual(f["attention_limit"], 20)
        self.assertEqual(
            f["include_sections"],
            [
                "summary",
                "attention_items",
                "recent_orders",
                "upcoming_tours",
                "recent_publications",
                "conversion_links",
            ],
        )

    def test_ops_dashboard_attention_links_execution_offer(self) -> None:
        user = self.create_user()
        tour = self.create_tour(departure_datetime=datetime.now(UTC) + timedelta(days=14))
        bp = self.create_boarding_point(tour)
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=offer.id, tour_id=tour.id, link_status="active"))
        order = self.create_order(
            user,
            tour,
            bp,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime.now(UTC) + timedelta(hours=2),
            total_amount=Decimal("50.00"),
        )
        self.session.flush()

        r = self.client.get("/admin/ops-dashboard", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertGreaterEqual(body["summary"]["active_holds_count"], 1)
        pay_pending = [x for x in body["attention_items"] if x.get("kind") == "payment_pending"]
        self.assertTrue(any(x.get("related_order_id") == order.id for x in pay_pending))
        hit = next(x for x in pay_pending if x["related_order_id"] == order.id)
        self.assertEqual(hit.get("related_supplier_offer_id"), offer.id)
        self.assertEqual(hit.get("related_tour_id"), tour.id)
        self.assertEqual(hit.get("admin_path"), f"/admin/orders/{order.id}")

    def test_ops_dashboard_lists_publication_and_conversion(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        tour = self.create_tour(status=TourStatus.OPEN_FOR_SALE)
        self.session.add(SupplierOfferExecutionLink(supplier_offer_id=offer.id, tour_id=tour.id, link_status="active"))
        self.session.add(
            SupplierOfferShowcasePublishAttempt(
                supplier_offer_id=offer.id,
                provider="telegram",
                channel_ref="-1001",
                status=SupplierOfferShowcasePublishAttemptStatus.PERSISTED,
                actor_surface=SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN,
                requested_by="admin:test",
                showcase_message_id=28,
            )
        )
        self.session.flush()

        r = self.client.get("/admin/ops-dashboard", headers=self._headers())
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        pubs = body["recent_publications"]
        self.assertTrue(any(p["supplier_offer_id"] == offer.id for p in pubs))
        hit_pub = next(p for p in pubs if p["supplier_offer_id"] == offer.id)
        self.assertEqual(hit_pub["admin_path"], f"/admin/supplier-offers/{offer.id}/review-package")
        links = body["conversion_links"]
        hit_link = next(l for l in links if l["tour_id"] == tour.id)
        self.assertEqual(hit_link["supplier_offer_admin_path"], f"/admin/supplier-offers/{offer.id}/review-package")
        self.assertEqual(hit_link["tour_admin_path"], f"/admin/tours/{tour.id}")
        self.assertEqual(hit_link["admin_path"], f"/admin/supplier-offers/{offer.id}/review-package")
        self.assertTrue(any(l["execution_link_id"] and l["tour_id"] == tour.id for l in links))

    def test_ops_dashboard_invalid_include_sections_422(self) -> None:
        r = self.client.get(
            "/admin/ops-dashboard",
            params={"include_sections": "summary,bogus"},
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_ops_dashboard_include_sections_summary_only_lists_empty(self) -> None:
        user = self.create_user()
        tour = self.create_tour(departure_datetime=datetime.now(UTC) + timedelta(days=14))
        bp = self.create_boarding_point(tour)
        self.create_order(
            user,
            tour,
            bp,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime.now(UTC) + timedelta(hours=2),
            total_amount=Decimal("50.00"),
        )
        self.session.flush()

        r = self.client.get(
            "/admin/ops-dashboard",
            params={"include_sections": "summary"},
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["filters"]["include_sections"], ["summary"])
        self.assertGreaterEqual(body["summary"]["active_holds_count"], 1)
        self.assertEqual(body["attention_items"], [])
        self.assertEqual(body["recent_orders"], [])
        self.assertEqual(body["upcoming_tours"], [])
        self.assertEqual(body["recent_publications"], [])
        self.assertEqual(body["conversion_links"], [])

    def test_ops_dashboard_days_ahead_limits_upcoming(self) -> None:
        self.create_tour(
            departure_datetime=datetime.now(UTC) + timedelta(days=200),
            status=TourStatus.DRAFT,
        )
        near = self.create_tour(
            departure_datetime=datetime.now(UTC) + timedelta(days=5),
            status=TourStatus.DRAFT,
        )
        self.session.flush()

        r = self.client.get(
            "/admin/ops-dashboard",
            params={
                "include_sections": "upcoming_tours",
                "days_ahead": 30,
                "tours_limit": 50,
            },
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        codes = {t["code"] for t in body["upcoming_tours"]}
        self.assertIn(near.code, codes)
        self.assertEqual(body["summary"]["upcoming_tours_count"], 1)

    def test_ops_dashboard_recent_days_filters_publications(self) -> None:
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        fresh = SupplierOfferShowcasePublishAttempt(
            supplier_offer_id=offer.id,
            provider="telegram",
            channel_ref="-1001",
            status=SupplierOfferShowcasePublishAttemptStatus.PERSISTED,
            actor_surface=SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN,
            requested_by="admin:test",
        )
        stale = SupplierOfferShowcasePublishAttempt(
            supplier_offer_id=offer.id,
            provider="telegram",
            channel_ref="-1002",
            status=SupplierOfferShowcasePublishAttemptStatus.PERSISTED,
            actor_surface=SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN,
            requested_by="admin:test",
        )
        self.session.add(fresh)
        self.session.add(stale)
        self.session.flush()
        self.session.execute(
            update(SupplierOfferShowcasePublishAttempt)
            .where(SupplierOfferShowcasePublishAttempt.id == stale.id)
            .values(created_at=datetime.now(UTC) - timedelta(days=30))
        )
        self.session.flush()

        r = self.client.get(
            "/admin/ops-dashboard",
            params={"include_sections": "recent_publications", "recent_days": 7},
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        ids = {p["publish_attempt_id"] for p in r.json()["recent_publications"]}
        self.assertIn(fresh.id, ids)
        self.assertNotIn(stale.id, ids)

    def test_ops_dashboard_b16c_recent_orders_have_admin_path(self) -> None:
        user = self.create_user()
        tour = self.create_tour(departure_datetime=datetime.now(UTC) + timedelta(days=14))
        bp = self.create_boarding_point(tour)
        order = self.create_order(
            user,
            tour,
            bp,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.AWAITING_PAYMENT,
            cancellation_status=CancellationStatus.ACTIVE,
            reservation_expires_at=datetime.now(UTC) + timedelta(hours=2),
            total_amount=Decimal("50.00"),
        )
        self.session.flush()

        r = self.client.get(
            "/admin/ops-dashboard",
            params={"include_sections": "recent_orders"},
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        rows = [x for x in r.json()["recent_orders"] if x["id"] == order.id]
        self.assertTrue(rows)
        self.assertEqual(rows[0]["admin_path"], f"/admin/orders/{order.id}")

    def test_ops_dashboard_b16c_upcoming_tours_have_admin_path(self) -> None:
        near = self.create_tour(
            departure_datetime=datetime.now(UTC) + timedelta(days=5),
            status=TourStatus.DRAFT,
        )
        self.session.flush()

        r = self.client.get(
            "/admin/ops-dashboard",
            params={"include_sections": "upcoming_tours", "days_ahead": 30, "tours_limit": 50},
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        rows = [t for t in r.json()["upcoming_tours"] if t["code"] == near.code]
        self.assertTrue(rows)
        self.assertEqual(rows[0]["admin_path"], f"/admin/tours/{near.id}")

    def test_ops_dashboard_b16c_attention_failed_publish_review_package_path(self) -> None:
        # showcase_publish_failed attention uses supplier offer review-package (same as recent_publications rows).
        supplier = self.create_supplier()
        offer = self.create_supplier_offer(supplier)
        self.session.add(
            SupplierOfferShowcasePublishAttempt(
                supplier_offer_id=offer.id,
                provider="telegram",
                channel_ref="-1001",
                status=SupplierOfferShowcasePublishAttemptStatus.FAILED,
                actor_surface=SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN,
                requested_by="admin:test",
                error_code="channel_denied",
            )
        )
        self.session.flush()

        r = self.client.get(
            "/admin/ops-dashboard",
            params={"include_sections": "attention_items"},
            headers=self._headers(),
        )
        self.assertEqual(r.status_code, 200, r.text)
        failed = [x for x in r.json()["attention_items"] if x.get("kind") == "showcase_publish_failed"]
        self.assertTrue(failed)
        hit = next(x for x in failed if x.get("related_supplier_offer_id") == offer.id)
        self.assertEqual(hit["admin_path"], f"/admin/supplier-offers/{offer.id}/review-package")
