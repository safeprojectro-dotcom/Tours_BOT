"""Track 3: moderation, publication payload, supplier cannot bypass platform gate."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event, select

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.enums import (
    SupplierOfferLifecycle,
    SupplierOfferShowcasePublishActorSurface,
    SupplierOfferShowcasePublishAttemptStatus,
    TourSalesMode,
)
from app.models.supplier import SupplierOfferExecutionLink
from app.models.supplier import Supplier, SupplierOffer
from app.models.supplier_notification_outbox import SupplierNotificationOutbox
from app.models.supplier_offer_showcase_publish_attempt import SupplierOfferShowcasePublishAttempt
from app.models.supplier_offer_tour_bridge import SupplierOfferTourBridge
from app.models.tour import Tour
from app.services.supplier_offer_deep_link import (
    parse_supplier_offer_start_arg,
    private_bot_deeplink,
    supplier_offer_start_payload,
)
from app.services.supplier_offer_showcase_message import format_supplier_offer_showcase_html
from app.services.telegram_showcase_client import TelegramShowcaseSendError
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
                "included_text": "Meals and transport",
                "excluded_text": "Tips and personal expenses",
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

    def _approve_packaging_via_http(self, oid: int, headers: dict[str, str]) -> None:
        """B15C helper: generate + approve packaging (accept warnings if needed)."""
        g = self.client.post(f"/admin/supplier-offers/{oid}/packaging/generate", headers=headers)
        self.assertEqual(g.status_code, 200, g.text)
        a = self.client.post(
            f"/admin/supplier-offers/{oid}/packaging/approve",
            headers=headers,
            json={"accept_warnings": True},
        )
        self.assertEqual(a.status_code, 200, a.text)

    def _b15c_bridge_and_activate_catalog(
        self,
        oid: int,
        headers: dict[str, str],
        *,
        existing_tour_id: int | None = None,
    ) -> tuple[int, str]:
        """After moderation approve: tour bridge + activate-for-catalog. No execution link."""
        payload: dict[str, int] = {}
        if existing_tour_id is not None:
            payload["existing_tour_id"] = existing_tour_id
        br = self.client.post(
            f"/admin/supplier-offers/{oid}/tour-bridge",
            headers=headers,
            json=payload,
        )
        self.assertEqual(br.status_code, 200, br.text)
        tour_id = int(br.json()["tour_id"])
        tour_row = self.session.get(Tour, tour_id)
        self.assertIsNotNone(tour_row)
        assert tour_row is not None
        tour_code = (tour_row.code or "").strip()
        act = self.client.post(f"/admin/tours/{tour_id}/activate-for-catalog", headers=headers, json={})
        self.assertEqual(act.status_code, 200, act.text)
        return tour_id, tour_code

    def _b15c_bridge_activate_and_execution_link(
        self,
        oid: int,
        headers: dict[str, str],
        *,
        existing_tour_id: int | None = None,
    ) -> tuple[int, str]:
        """Approved offer → bridge → catalog activation → active execution link."""
        tour_id, tour_code = self._b15c_bridge_and_activate_catalog(
            oid,
            headers,
            existing_tour_id=existing_tour_id,
        )
        lk = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_id},
        )
        self.assertEqual(lk.status_code, 200, lk.text)
        return tour_id, tour_code

    def _supersede_active_bridge_to_tour(self, offer_id: int, new_tour_id: int) -> None:
        """Point the active supplier-offer bridge at another tour (no public API yet; DB-local test utility)."""
        cur = (
            self.session.query(SupplierOfferTourBridge)
            .filter(
                SupplierOfferTourBridge.supplier_offer_id == offer_id,
                SupplierOfferTourBridge.status == "active",
            )
            .one()
        )
        cur.status = "superseded"
        offer = self.session.get(SupplierOffer, offer_id)
        self.assertIsNotNone(offer)
        assert offer is not None
        self.session.add(
            SupplierOfferTourBridge(
                supplier_offer_id=offer_id,
                tour_id=new_tour_id,
                status="active",
                bridge_kind="linked_existing_tour",
                created_by="unit-test",
                source_packaging_status=offer.packaging_status.value,
                source_lifecycle_status=offer.lifecycle_status.value,
                packaging_snapshot_json={},
                notes="unit-test bridge supersede",
            ),
        )
        self.session.flush()

    def _prepare_offer_for_channel_publish(
        self,
        oid: int,
        headers: dict[str, str],
        *,
        existing_tour_id: int | None = None,
    ) -> tuple[int, str]:
        """B15C: packaging → moderation approve → bridge → catalog → execution link (still approved, not published)."""
        self._approve_packaging_via_http(oid, headers)
        a = self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        self.assertEqual(a.status_code, 200, a.text)
        return self._b15c_bridge_activate_and_execution_link(
            oid,
            headers,
            existing_tour_id=existing_tour_id,
        )

    def test_moderation_approve_reject_publish_mock_telegram(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}

        bad = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(bad.status_code, 400)

        self._prepare_offer_for_channel_publish(oid, headers)

        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch(
                "app.services.telegram_showcase_client.send_showcase_publication",
                return_value=42,
            ),
        ):
            p = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(p.status_code, 200, p.text)
        pub = p.json()
        self.assertEqual(pub["offer"]["lifecycle_status"], "published")
        self.assertEqual(pub["telegram_message_id"], 42)

        attempt = self.session.scalar(
            select(SupplierOfferShowcasePublishAttempt).where(
                SupplierOfferShowcasePublishAttempt.supplier_offer_id == oid,
            ),
        )
        self.assertIsNotNone(attempt)
        assert attempt is not None
        self.assertEqual(attempt.status, SupplierOfferShowcasePublishAttemptStatus.PERSISTED)
        self.assertEqual(attempt.actor_surface, SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN)
        self.assertEqual(attempt.showcase_chat_id, "-10012345")
        self.assertEqual(attempt.showcase_message_id, 42)
        self.assertIsNotNone(attempt.payload_fingerprint)
        self.assertEqual(attempt.requested_by, "http_admin")

        ob = self.session.scalar(
            select(SupplierNotificationOutbox).where(
                SupplierNotificationOutbox.idempotency_key
                == f"s1c1:supplier_offer_published:supplier_offer:{oid}",
            ),
        )
        self.assertIsNotNone(ob)
        assert ob is not None
        self.assertEqual(ob.event_type, "supplier_offer_published")
        self.assertEqual(ob.actor_surface, "s1c3_after_showcase_channel_publish")

        dup = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(dup.status_code, 400)

    def test_publish_sends_text_only_when_cover_is_google_share_link_b15c4(self) -> None:
        """Non-sendable HTTPS cover must not be passed to sendPhoto; publish uses sendMessage."""
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour_id, _tour_code = self._prepare_offer_for_channel_publish(oid, headers)
        self.assertGreater(tour_id, 0)

        c = self.client.put(
            f"/admin/supplier-offers/{oid}/cover",
            headers=headers,
            json={"cover_media_reference": "https://share.google/aslSRRhI6yMkRSuMV"},
        )
        self.assertEqual(c.status_code, 200, c.text)

        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch(
                "app.services.telegram_showcase_client.send_showcase_publication",
                return_value=99,
            ) as send_mock,
        ):
            p = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(p.status_code, 200, p.text)
        send_mock.assert_called_once()
        self.assertIsNone(send_mock.call_args.kwargs.get("photo_url"))

    def test_publish_failed_audit_attempt_when_telegram_send_errors(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        self._prepare_offer_for_channel_publish(oid, headers)
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch(
                "app.services.telegram_showcase_client.send_showcase_publication",
                side_effect=TelegramShowcaseSendError("bot blocked"),
            ),
        ):
            p = self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self.assertEqual(p.status_code, 400, p.text)
        attempt = self.session.scalar(
            select(SupplierOfferShowcasePublishAttempt).where(
                SupplierOfferShowcasePublishAttempt.supplier_offer_id == oid,
            ),
        )
        self.assertIsNotNone(attempt)
        assert attempt is not None
        self.assertEqual(attempt.status, SupplierOfferShowcasePublishAttemptStatus.FAILED)
        self.assertEqual(attempt.actor_surface, SupplierOfferShowcasePublishActorSurface.HTTP_ADMIN)
        self.assertEqual(attempt.error_code, "telegram_showcase_send")
        self.assertEqual(attempt.requested_by, "http_admin")

        ob_failed = self.session.scalar(
            select(SupplierNotificationOutbox).where(
                SupplierNotificationOutbox.supplier_offer_id == oid,
            ),
        )
        self.assertIsNone(ob_failed)

    def test_approve_is_not_auto_publish_and_retract_is_separate_action(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}

        self._approve_packaging_via_http(oid, headers)
        a = self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        self.assertEqual(a.status_code, 200, a.text)
        self.assertEqual(a.json()["lifecycle_status"], "approved")
        self.assertIsNone(a.json()["published_at"])

        bad_retract = self.client.post(f"/admin/supplier-offers/{oid}/retract", headers=headers)
        self.assertEqual(bad_retract.status_code, 400)

        self._b15c_bridge_activate_and_execution_link(oid, headers)

        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.telegram_showcase_client.send_showcase_publication", return_value=77),
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
            patch("app.services.telegram_showcase_client.send_showcase_publication", return_value=90),
            patch("app.services.supplier_offer_moderation_service.delete_channel_message", return_value=True),
            patch("app.services.supplier_offer_supplier_notification_service.get_settings", return_value=mock_cfg),
            patch("app.services.supplier_offer_supplier_notification_service.send_private_text_message", return_value=123) as notify_send,
        ):
            self._approve_packaging_via_http(oid, headers)
            self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
            self._b15c_bridge_activate_and_execution_link(oid, headers)
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
        """B15C: execution link must match active bridge; replacing target requires bridge + catalog to move first."""
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
        self._approve_packaging_via_http(oid, headers)
        self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        self._b15c_bridge_and_activate_catalog(oid, headers, existing_tour_id=tour_a.id)
        self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_a.id},
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.telegram_showcase_client.send_showcase_publication", return_value=120),
        ):
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)

        r1 = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_a.id},
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r1.json()["link_status"], "active")
        self.assertEqual(r1.json()["tour_id"], tour_a.id)

        r_same = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_a.id},
        )
        self.assertEqual(r_same.status_code, 200, r_same.text)
        self.assertEqual(r_same.json()["tour_id"], tour_a.id)

        self._supersede_active_bridge_to_tour(oid, tour_b.id)
        ab = self.client.post(f"/admin/tours/{tour_b.id}/activate-for-catalog", headers=headers, json={})
        self.assertEqual(ab.status_code, 200, ab.text)
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
        self._prepare_offer_for_channel_publish(oid, headers, existing_tour_id=tour.id)
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.telegram_showcase_client.send_showcase_publication", return_value=121),
        ):
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)

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

    def test_execution_link_requires_packaging_and_bridge_before_publish(self) -> None:
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
        self.assertIn("Packaging must be approved for publish before execution link.", r.text)

    def test_execution_link_rejects_unknown_tour(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour_ok = self.create_tour(code="LNK-REAL", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()
        self._approve_packaging_via_http(oid, headers)
        self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        self._b15c_bridge_and_activate_catalog(oid, headers, existing_tour_id=tour_ok.id)

        r = self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": 999999},
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("active supplier-offer tour bridge", r.text)

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
        self._approve_packaging_via_http(oid, headers)
        self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        self._b15c_bridge_and_activate_catalog(oid, headers, existing_tour_id=tour_a.id)
        self.client.post(
            f"/admin/supplier-offers/{oid}/execution-link",
            headers=headers,
            json={"tour_id": tour_a.id, "link_note": "initial"},
        )
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.telegram_showcase_client.send_showcase_publication", return_value=123),
        ):
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)
        self._supersede_active_bridge_to_tour(oid, tour_b.id)
        acb = self.client.post(f"/admin/tours/{tour_b.id}/activate-for-catalog", headers=headers, json={})
        self.assertEqual(acb.status_code, 200, acb.text)
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

    def test_operator_execution_link_workflow_routes_create_replace_close_and_list(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        mock_cfg = SimpleNamespace(
            telegram_bot_token="dummy-token",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_username="testbot",
            telegram_mini_app_url="https://example.com/mini",
        )
        tour_a = self.create_tour(code="LNK-WF-A", sales_mode=TourSalesMode.PER_SEAT)
        tour_b = self.create_tour(code="LNK-WF-B", sales_mode=TourSalesMode.PER_SEAT)
        self.session.commit()
        self._approve_packaging_via_http(oid, headers)
        self.client.post(f"/admin/supplier-offers/{oid}/moderation/approve", headers=headers)
        self._b15c_bridge_and_activate_catalog(oid, headers, existing_tour_id=tour_a.id)
        with (
            patch("app.services.supplier_offer_moderation_service.get_settings", return_value=mock_cfg),
            patch("app.services.telegram_showcase_client.send_showcase_publication", return_value=124),
        ):
            created = self.client.post(
                f"/admin/supplier-offers/{oid}/link-tour",
                headers=headers,
                json={"tour_id": tour_a.id, "link_note": "initial"},
            )
            self.assertEqual(created.status_code, 200, created.text)
            self.client.post(f"/admin/supplier-offers/{oid}/publish", headers=headers)

        self.assertEqual(created.json()["link_status"], "active")
        self.assertEqual(created.json()["tour_id"], tour_a.id)

        duplicate_create = self.client.post(
            f"/admin/supplier-offers/{oid}/link-tour",
            headers=headers,
            json={"tour_id": tour_a.id},
        )
        self.assertEqual(duplicate_create.status_code, 400)
        self.assertIn("Active execution link already exists", duplicate_create.text)

        self._supersede_active_bridge_to_tour(oid, tour_b.id)
        acb = self.client.post(f"/admin/tours/{tour_b.id}/activate-for-catalog", headers=headers, json={})
        self.assertEqual(acb.status_code, 200, acb.text)
        replaced = self.client.post(
            f"/admin/supplier-offers/{oid}/replace-link",
            headers=headers,
            json={"tour_id": tour_b.id, "link_note": "replacement"},
        )
        self.assertEqual(replaced.status_code, 200, replaced.text)
        self.assertEqual(replaced.json()["link_status"], "active")
        self.assertEqual(replaced.json()["tour_id"], tour_b.id)

        history = self.client.get(f"/admin/supplier-offers/{oid}/links", headers=headers)
        self.assertEqual(history.status_code, 200, history.text)
        body = history.json()
        self.assertEqual(body["total_returned"], 2)
        active_items = [item for item in body["items"] if item["link_status"] == "active"]
        self.assertEqual(len(active_items), 1)
        self.assertEqual(active_items[0]["tour_id"], tour_b.id)
        closed_items = [item for item in body["items"] if item["link_status"] == "closed"]
        self.assertEqual(len(closed_items), 1)
        self.assertEqual(closed_items[0]["close_reason"], "replaced")

        closed = self.client.post(
            f"/admin/supplier-offers/{oid}/close-link",
            headers=headers,
            json={"reason": "unlinked"},
        )
        self.assertEqual(closed.status_code, 200, closed.text)
        self.assertEqual(closed.json()["link_status"], "closed")
        self.assertEqual(closed.json()["close_reason"], "unlinked")

        links = self.session.query(SupplierOfferExecutionLink).filter_by(supplier_offer_id=oid).all()
        active_after_close = [link for link in links if link.link_status == "active"]
        self.assertEqual(active_after_close, [])

    def test_admin_showcase_preview_read_only_matches_template(self) -> None:
        """B12/B13.4: GET showcase-preview builds caption + CTA URLs; does not call Telegram."""
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        mock_cfg = SimpleNamespace(
            telegram_bot_username="previewbot",
            telegram_mini_app_url="https://example.com/app",
            telegram_offer_showcase_channel_id="",
            telegram_bot_token="",
        )
        with (
            patch(
                "app.services.supplier_offer_moderation_service.get_settings",
                return_value=mock_cfg,
            ),
            patch("app.services.telegram_showcase_client._post_telegram_api") as tg_send,
        ):
            r = self.client.get(f"/admin/supplier-offers/{oid}/showcase-preview", headers=headers)
        tg_send.assert_not_called()
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["supplier_offer_id"], oid)
        self.assertEqual(body["lifecycle_status"], "ready_for_moderation")
        self.assertFalse(body["can_publish_now"])
        self.assertGreater(len(body["warnings"]), 0)
        self.assertTrue(any("Only approved" in w for w in body["warnings"]))
        self.assertEqual(body["publication_mode"], "text_only")
        self.assertIsNone(body["showcase_photo_url"])
        self.assertTrue(body["disable_web_page_preview"])
        self.assertIn("https://t.me/previewbot?start=supoffer_", body["cta_detalii_href"])
        self.assertIn(f"/supplier-offers/{oid}", body["cta_rezerva_href"])
        self.assertIn("<a ", body["caption_html"])
        self.assertIn("Previzualizare", body["preview_notice"])

    def test_admin_showcase_preview_can_publish_when_approved_and_config_complete(self) -> None:
        """B15C: can_publish_now when gates + active execution link; Rezervă preview is exact /tours/{code}."""
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour_id, tour_code = self._prepare_offer_for_channel_publish(oid, headers)
        self.assertGreater(tour_id, 0)
        mock_cfg = SimpleNamespace(
            telegram_bot_username="previewbot",
            telegram_mini_app_url="https://example.com/app",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_token="secret-token-for-tests",
        )
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(f"/admin/supplier-offers/{oid}/showcase-preview", headers=headers)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["lifecycle_status"], "approved")
        self.assertTrue(body["can_publish_now"])
        self.assertEqual(body["warnings"], [])
        href = body.get("cta_rezerva_href") or ""
        self.assertIn(f"tour_{tour_code}", href)
        self.assertRegex(href, r"https://t\.me/previewbot\?startapp=tour_")

    def test_admin_showcase_preview_rezerva_uses_inline_mini_app_short_name_b15c5(self) -> None:
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        tour_id, tour_code = self._prepare_offer_for_channel_publish(oid, headers)
        self.assertGreater(tour_id, 0)
        mock_cfg = SimpleNamespace(
            telegram_bot_username="previewbot",
            telegram_mini_app_url="https://example.com/app",
            telegram_mini_app_short_name="appshort",
            telegram_offer_showcase_channel_id="-10012345",
            telegram_bot_token="secret-token-for-tests",
        )
        with patch(
            "app.services.supplier_offer_moderation_service.get_settings",
            return_value=mock_cfg,
        ):
            r = self.client.get(f"/admin/supplier-offers/{oid}/showcase-preview", headers=headers)
        self.assertEqual(r.status_code, 200, r.text)
        href = r.json().get("cta_rezerva_href") or ""
        self.assertIn(tour_code, href)
        self.assertRegex(href, r"https://t\.me/previewbot/appshort\?startapp=tour_")

    def test_admin_showcase_preview_404_unknown_offer(self) -> None:
        r = self.client.get(
            "/admin/supplier-offers/999999001/showcase-preview",
            headers={"Authorization": "Bearer test-admin-secret"},
        )
        self.assertEqual(r.status_code, 404)

    def test_admin_showcase_channel_payload_read_only_matches_adapter_shape(self) -> None:
        """B13D-alt: GET showcase-channel-payload mirrors ShowcaseChannelPublishRequest; no Telegram."""
        _, token = self._bootstrap_supplier_token()
        oid = self._ready_offer(token)
        headers = {"Authorization": "Bearer test-admin-secret"}
        mock_cfg = SimpleNamespace(
            telegram_offer_showcase_channel_id="-100777",
            telegram_bot_token="not-used",
            telegram_bot_username="x",
            telegram_mini_app_url="https://ex/m",
        )
        with (
            patch(
                "app.services.supplier_offer_moderation_service.get_settings",
                return_value=mock_cfg,
            ),
            patch("app.services.telegram_showcase_client._post_telegram_api") as tg_send,
        ):
            r = self.client.get(f"/admin/supplier-offers/{oid}/showcase-channel-payload", headers=headers)
        tg_send.assert_not_called()
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["supplier_offer_id"], oid)
        self.assertEqual(body["provider"], "telegram_showcase_channel")
        self.assertEqual(body["channel_ref"], "-100777")
        self.assertIsNone(body["idempotency_key"])
        self.assertIn("caption_html", body["publication"])
        self.assertTrue(body["disable_web_page_preview"])
        self.assertIn("nothing was sent", body["preview_notice"].lower())

    def test_admin_showcase_channel_payload_404_unknown_offer(self) -> None:
        r = self.client.get(
            "/admin/supplier-offers/999999002/showcase-channel-payload",
            headers={"Authorization": "Bearer test-admin-secret"},
        )
        self.assertEqual(r.status_code, 404)

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
        self.assertIn("📅", html)
        self.assertIn("Abonează-te la canal", html)
        self.assertNotIn("<test>", html)  # escaped
        self.assertRegex(html, r'href="https://t\.me/mybot\?start=supoffer_')
        self.assertRegex(html, r'href="https://t\.me/mybot/myapp/supplier-offers/\d+"')

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
