"""Ops queue read API and service (Phase 5 Step 15)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.api.ops_queue_auth import require_ops_queue_token
from app.db.session import get_db
from app.main import create_app
from app.models.enums import TourStatus
from app.models.handoff import Handoff
from app.models.waitlist import WaitlistEntry
from app.services.ops_queue_read import OpsQueueReadService
from tests.unit.base import FoundationDBTestCase


class OpsQueueServiceTests(FoundationDBTestCase):
    def test_open_handoffs_fifo_and_order_tour_labels(self) -> None:
        user = self.create_user()
        tour = self.create_tour(code="OPS-H1", title_default="Ops Tour One")
        bp = self.create_boarding_point(tour)
        order = self.create_order(user, tour, bp)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=order.id,
                reason="mini_app_support|payment",
                priority="normal",
                status="open",
                assigned_operator_id=None,
            )
        )
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=None,
                reason="private_chat_contact",
                priority="normal",
                status="open",
                assigned_operator_id=None,
            )
        )
        self.session.commit()

        svc = OpsQueueReadService()
        out = svc.open_handoffs(self.session)
        self.assertEqual(out.ordering, "created_at_asc")
        self.assertEqual(len(out.items), 2)
        self.assertEqual(out.items[0].reason, "mini_app_support|payment")
        self.assertEqual(out.items[0].order_id, order.id)
        self.assertEqual(out.items[0].order_tour_code, "OPS-H1")
        self.assertEqual(out.items[0].order_tour_title_default, "Ops Tour One")
        self.assertIsNone(out.items[1].order_id)
        self.assertIsNone(out.items[1].order_tour_code)

    def test_open_handoffs_skips_closed_status(self) -> None:
        user = self.create_user()
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=None,
                reason="x",
                priority="normal",
                status="closed",
                assigned_operator_id=None,
            )
        )
        self.session.commit()
        out = OpsQueueReadService().open_handoffs(self.session)
        self.assertEqual(len(out.items), 0)

    def test_active_waitlist_only_active_status(self) -> None:
        user = self.create_user()
        tour = self.create_tour(code="WL-OPS", title_default="Waitlist Tour")
        self.session.add(
            WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=2, status="active"),
        )
        self.session.add(
            WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=1, status="cancelled"),
        )
        self.session.commit()
        out = OpsQueueReadService().active_waitlist(self.session)
        self.assertEqual(len(out.items), 1)
        self.assertEqual(out.items[0].tour_code, "WL-OPS")
        self.assertEqual(out.items[0].status, "active")


class OpsQueueAPITests(FoundationDBTestCase):
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

        def override_get_db():
            yield self.session

        self.app.dependency_overrides[get_db] = override_get_db
        self.app.dependency_overrides[require_ops_queue_token] = lambda: None
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.app.dependency_overrides.clear()
        event.remove(self.session, "after_transaction_end", self._restart_savepoint)
        super().tearDown()

    def test_handoffs_endpoint_returns_json(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="API-H",
            title_default="Api Handoff Tour",
            departure_datetime=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 5, 2, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        bp = self.create_boarding_point(tour)
        order = self.create_order(user, tour, bp)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=order.id,
                reason="test",
                priority="normal",
                status="open",
                assigned_operator_id=None,
            )
        )
        self.session.commit()

        r = self.client.get("/internal/ops/handoffs/open")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["ordering"], "created_at_asc")
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["items"][0]["order_tour_code"], "API-H")
        self.assertEqual(body["items"][0]["reason"], "test")

    def test_waitlist_endpoint_returns_json(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="API-W",
            title_default="Api Waitlist Tour",
            departure_datetime=datetime(2026, 5, 3, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 5, 4, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        self.session.add(WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=3, status="active"))
        self.session.commit()

        r = self.client.get("/internal/ops/waitlist/active")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["items"][0]["tour_code"], "API-W")
        self.assertEqual(body["items"][0]["seats_count"], 3)

    def test_unauthorized_without_valid_token(self) -> None:
        self.app.dependency_overrides.pop(require_ops_queue_token, None)
        with patch("app.api.ops_queue_auth.get_settings") as m:
            m.return_value.ops_queue_token = "expected-secret-token"
            r = self.client.get("/internal/ops/handoffs/open")
            self.assertEqual(r.status_code, 401)

    def test_disabled_when_token_unset(self) -> None:
        self.app.dependency_overrides.pop(require_ops_queue_token, None)
        with patch("app.api.ops_queue_auth.get_settings") as m:
            m.return_value.ops_queue_token = None
            r = self.client.get("/internal/ops/handoffs/open")
            self.assertEqual(r.status_code, 503)
