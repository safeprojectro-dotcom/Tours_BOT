"""Track 3: moderation, publication payload, supplier cannot bypass platform gate."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import SupplierOfferLifecycle, TourSalesMode
from app.models.supplier import SupplierOfferExecutionLink
from app.models.supplier import Supplier
from app.services.supplier_offer_deep_link import (
    parse_supplier_offer_start_arg,
    private_bot_deeplink,
    supplier_offer_start_payload,
)
from app.services.supplier_offer_showcase_message import format_supplier_offer_showcase_html
from tests.unit.base import FoundationDBTestCase


class SupplierOfferTrack3ModerationTests(FoundationDBTestCase):
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
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def _bootstrap_supplier_token(self) -> tuple[int, str]:
        r = self.client.post(
            "/admin/suppliers",
            headers={"Authorization": "Bearer test-admin-secret"},
            json={"code": "PUB-1", "display_name": "Publisher"},
        )
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        return body["supplier"]["id"], body["api_token"]

    def _ready_offer(self, token: str) -> int:
        dep = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        ret = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
        c = self.client.post(
            "/supplier-admin/offers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Showcase Trip",
                "description": "Nice trip",
                "program_text": "Day 1 …",
                "departure_datetime": dep.isoformat(),
                "return_datetime": ret.isoformat(),
                "vehicle_label": "Coach",
                "seats_total": 40,
                "base_price": "120.00",
                "currency": "EUR",
                "sales_mode": "per_seat",
            },
        )
        self.assertEqual(c.status_code, 201, c.text)
        oid = c.json()["id"]
        u = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"lifecycle_status": "ready_for_moderation"},
        )
        self.assertEqual(u.status_code, 200, u.text)
        return oid

    def test_moderation_approve_reject_publish_mock_telegram(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}

        bad = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(bad.status_code, 400)

        a = self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        self.assertEqual(a.status_code, 200, a.text)
        self.assertEqual(a.json()["lifecycle_status"], "approved")

        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch(
                "app.services.supplier_offer_moderation_service.send_showcase_publication",
                return_value=42,
            ),
        ):
            p = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(p.status_code, 200, p.text)
        pub = p.json()
        self.assertEqual(pub["offer"]["lifecycle_status"], "published")
        self.assertEqual(pub["telegram_message_id"], 42)

        dup = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(dup.status_code, 400)

    def test_approve_is_not_auto_publish_and_retract_is_separate_action(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}

        a = self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        self.assertEqual(a.status_code, 200, a.text)
        self.assertEqual(a.json()["lifecycle_status"], "approved")
        self.assertIsNone(a.json()["published_at"])

        bad_retract = self.client.post(f"/admin/supplier-offers/{oid}/retract", headers=headers)
        self.assertEqual(bad_retract.status_code, 400)

        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.supplier_offer_moderation_service.send_showcase_publication", return_value=77),
            patch("app.services.supplier_offer_moderation_service.delete_channel_message", return_value=True),
        ):
            p = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
            self.assertEqual(p.status_code, 200, p.text)
            self.assertEqual(p.json()["offer"]["lifecycle_status"], "published")
            r = self.client.post(f"/admin/supplier-offers/{oid}/retract", headers=headers)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()["lifecycle_status"], "approved")

    def test_supplier_notifications_sent_for_moderation_and_publication_events(self) -> None:
        supplier_id, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        # Bind supplier to Telegram user for notifications.
        sup_row = self.session.get(Supplier, supplier_id)
        self.assertIsNotNone(sup_row)
        assert sup_row is not None
        sup_row.primary_telegram_user_id = 991001
        self.create_user(
            telegram_user_id=991001,
            username="notif_supplier",
            preferred_language="ro",
        )
        self.session.commit()

        headers = {"Authorization": "Bearer test-admin-secret"}
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.supplier_offer_moderation_service.send_showcase_publication", return_value=90),
            patch("app.services.supplier_offer_moderation_service.delete_channel_message", return_value=True),
            patch("app.services.supplier_offer_supplier_notification_service.send_private_text_message", return_value=123) as notify_send,
        ):
            self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
            self.client.post(f"/admin/supplier-offers/{oid}/retract", headers=headers)

        self.assertGreaterEqual(notify_send.call_count, 3)

    def test_reject_sets_reason(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        r = self.client.post(
            f"/admin/supplier-offers/{oid}/moderation/reject",
            headers=headers,
            json={"reason": "Fix dates"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["lifecycle_status"], "rejected")
        self.assertEqual(body["moderation_rejection_reason"], "Fix dates")

    def test_supplier_cannot_set_approved_or_publish(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        r = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"lifecycle_status": "approved"},
        )
        self.assertEqual(r.status_code, 400)

    def test_supplier_cannot_edit_approved_offer(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        r = self.client.put(
            f"/supplier-admin/offers/{oid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Hacked"},
        )
        self.assertEqual(r.status_code, 400)

    def test_admin_list_filter_by_lifecycle(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        lst = self.client.get(
            "/admin/supplier-offers",
            headers=headers,
            params={"lifecycle_status": "ready_for_moderation"},
        )
        self.assertEqual(lst.status_code, 200)
        ids = {x["id"] for x in lst.json()["items"]}
        self.assertIn(oid, ids)

    def test_admin_can_link_published_offer_to_tour_and_replace_active(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        tour_a = self.create_tour(code="LNK-A", sales_mode=TourSalesMode.PER_SEAT)
        tour_b = self.create_tour(code="LNK-B", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.supplier_offer_moderation_service.send_showcase_publication", return_value=120),
        ):
            self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)

        r1 = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_a.id},
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r1.json()["link_status"], "active")
        self.assertEqual(r1.json()["tour_id"], tour_a.id)

        # Re-linking same tour is idempotent and keeps one active link.
        r_same = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_a.id},
        )
        self.assertEqual(r_same.status_code, 200, r_same.text)
        self.assertEqual(r_same.json()["tour_id"], tour_a.id)

        r2 = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_b.id},
        )
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertEqual(r2.json()["tour_id"], tour_b.id)
        self.assertEqual(r2.json()["link_status"], "active")

        links = (
            self.session.query(SupplierOfferExecutionLink)
            .filter(SupplierOfferExecutionLink.supplier_offer_id == oid)
            .order_by(SupplierOfferExecutionLink.id.asc())
            .all()
        )
        self.assertGreaterEqual(len(links), 2)
        active = [x for x in links if x.link_status == "active"]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].tour_id, tour_b.id)
        replaced = [x for x in links if x.link_status == "closed" and x.close_reason == "replaced"]
        self.assertGreaterEqual(len(replaced), 1)

    def test_admin_can_close_active_execution_link_and_preserve_history(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        tour = self.create_tour(code="LNK-CLOSE", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.supplier_offer_moderation_service.send_showcase_publication", return_value=121),
        ):
            self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour.id},
        )

        close = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link/close",
            headers=headers,
            json={"reason": "unlinked"},
        )
        self.assertEqual(close.status_code, 200, close.text)
        self.assertEqual(close.json()["link_status"], "closed")
        self.assertEqual(close.json()["close_reason"], "unlinked")

        links = self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=oid).all()
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].link_status, "closed")
        self.assertEqual(links[0].close_reason, "unlinked")

    def test_execution_link_requires_published_offer(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour = self.create_tour(code="LNK-REQ", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()
        r = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour.id},
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("Only published offers", r.text)

    def test_execution_link_rejects_unknown_tour(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.supplier_offer_moderation_service.send_showcase_publication", return_value=122),
        ):
            self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)

        r = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": 999999},
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("Tour not found", r.text)

    def test_admin_can_list_execution_links_history(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        tour_a = self.create_tour(code="LNK-HIST-A", sales_mode=TourSalesMode.PER_SEAT)
        tour_b = self.create_tour(code="LNK-HIST-B", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.supplier_offer_moderation_service.send_showcase_publication", return_value=123),
        ):
            self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_a.id, "link_note": "initial"},
        )
        self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_b.id, "link_note": "replace"},
        )

        hist = self.client.get(f"/admin/supplier-offers/{oid}/execution-links", headers=headers)
        self.assertEqual(hist.status_code, 200, hist.text)
        body = hist.json()
        self.assertEqual(body["total_returned"], 2)
        self.assertEqual(body["items"][0]["tour_id"], tour_b.id)
        self.assertEqual(body["items"][0]["link_status"], "active")
        self.assertEqual(body["items"][1]["tour_id"], tour_a.id)
        self.assertEqual(body["items"][1]["link_status"], "closed")
        self.assertEqual(body["items"][1]["close_reason"], "replaced")

    def test_showcase_html_contains_cta_links(self) -> None:
        supplier = self.create_supplier(code="HTML-S")
        offer = self.create_supplier_offer(
            supplier,
            title="Bold <test> & Co",
            description="Desc",
            lifecycle_status=SupplierOfferLifecycle.APPROVED,
        )
        class _Cfg:
            telegram_bot_username = "mybot"
            telegram_mini_app_url = "https://t.me/mybot/myapp"

        html = format_supplier_offer_showcase_html(offer, _Cfg())  # type: ignore[arg-type]
        self.assertIn("Detalii", html)
        self.assertIn("Rezervă", html)
        self.assertIn("supoffer_", html)
        self.assertIn("Plecare:", html)
        self.assertIn("Întoarcere:", html)
        self.assertIn("Abonează-te la canal", html)
        self.assertNotIn("<test>", html)  # escaped
        self.assertRegex(html, r'href="https://t\.me/mybot\?start=supoffer_')
        self.assertRegex(html, r'href="https://t\.me/mybot/myapp"')

    def test_deep_link_helpers(self) -> None:
        self.assertEqual(supplier_offer_start_payload(7), "supoffer_7")
        self.assertEqual(parse_supplier_offer_start_arg("supoffer_7"), 7)
        self.assertIsNone(parse_supplier_offer_start_arg("tour_x"))
        self.assertEqual(
            private_bot_deeplink(bot_username="bot", offer_id=3),
            "https://t.me/bot?start=supoffer_3",
        )


class SupplierOfferTrack3RegressionTests(FoundationDBTestCase):
    """Layer A smoke: core tour catalog path unchanged."""

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
        self.client.close()
        self.app.dependency_overrides.clear()
        get_settings().admin_api_token = self._original_admin
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_admin_overview_unchanged(self) -> None:
        from app.models.enums import BookingStatus, CancellationStatus, PaymentStatus, TourStatus

        user = self.create_user()
        tour = self.create_tour(
            code="LAYER-A-1",
            status=TourStatus.OPEN_FOR_SALE,
            departure_datetime=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
            sales_mode=TourSalesMode.PER_SEAT,
        )
        point = self.create_boarding_point(tour)
        self.create_order(
            user,
            tour,
            point,
            booking_status=BookingStatus.RESERVED,
            payment_status=PaymentStatus.UNPAID,
            cancellation_status=CancellationStatus.CANCELLED_NO_PAYMENT,
            reservation_expires_at=None,
        )
        self.session.commit()
        r = self.client.get("/admin/overview", headers={"Authorization": "Bearer test-admin-secret"})
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.json()["tours_total_approx"], 1)
