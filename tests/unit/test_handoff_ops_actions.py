"""Handoff ops claim/close (Phase 5 Step 16)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.api.ops_queue_auth import require_ops_queue_token
from app.db.session import get_db
from app.main import create_app
from app.models.enums import TourStatus
from app.models.handoff import Handoff
from app.services.handoff_ops_actions import (
    HANDOFF_STATUS_CLOSED,
    HANDOFF_STATUS_IN_REVIEW,
    HANDOFF_STATUS_OPEN,
    HandoffOpsActionService,
)
from tests.unit.base import FoundationDBTestCase


class HandoffOpsActionServiceTests(FoundationDBTestCase):
    def test_claim_without_operator_sets_in_review(self) -> None:
        user = self.create_user()
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason="r0",
            priority="normal",
            status=HANDOFF_STATUS_OPEN,
            assigned_operator_id=None,
        )
        self.session.add(h)
        self.session.commit()
        row = HandoffOpsActionService().claim(self.session, handoff_id=h.id, operator_id=None)
        self.assertEqual(row.status, HANDOFF_STATUS_IN_REVIEW)
        self.assertIsNone(row.assigned_operator_id)

    def test_claim_then_conflict(self) -> None:
        user = self.create_user()
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason="r",
            priority="normal",
            status=HANDOFF_STATUS_OPEN,
            assigned_operator_id=None,
        )
        self.session.add(h)
        self.session.commit()
        hid = h.id

        svc = HandoffOpsActionService()
        op = self.create_user(telegram_user_id=88_001, username="operator_a")
        row = svc.claim(self.session, handoff_id=hid, operator_id=op.id)
        self.assertEqual(row.status, HANDOFF_STATUS_IN_REVIEW)
        self.assertEqual(row.assigned_operator_id, op.id)

        from app.services.handoff_ops_actions import HandoffClaimStateError

        with self.assertRaises(HandoffClaimStateError) as ctx:
            svc.claim(self.session, handoff_id=hid, operator_id=op.id)
        self.assertEqual(ctx.exception.current_status, HANDOFF_STATUS_IN_REVIEW)

    def test_close_from_open_and_conflict_when_closed(self) -> None:
        user = self.create_user()
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason="r2",
            priority="normal",
            status=HANDOFF_STATUS_OPEN,
            assigned_operator_id=None,
        )
        self.session.add(h)
        self.session.commit()
        hid = h.id
        svc = HandoffOpsActionService()
        op = self.create_user(telegram_user_id=88_002, username="operator_b")
        closed = svc.close(self.session, handoff_id=hid, operator_id=op.id)
        self.assertEqual(closed.status, HANDOFF_STATUS_CLOSED)
        self.assertEqual(closed.assigned_operator_id, op.id)

        from app.services.handoff_ops_actions import HandoffCloseStateError

        with self.assertRaises(HandoffCloseStateError):
            svc.close(self.session, handoff_id=hid)


class HandoffOpsAPITests(FoundationDBTestCase):
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

    def test_claim_close_flow_and_open_queue(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="HO-API",
            title_default="Handoff Ops",
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 6, 2, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        bp = self.create_boarding_point(tour)
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason="api_flow",
            priority="normal",
            status=HANDOFF_STATUS_OPEN,
            assigned_operator_id=None,
        )
        self.session.add(h)
        self.session.commit()
        hid = h.id
        op = self.create_user(telegram_user_id=99_001, username="ops_user")

        r0 = self.client.get("/internal/ops/handoffs/open")
        self.assertEqual(len(r0.json()["items"]), 1)

        r1 = self.client.patch(f"/internal/ops/handoffs/{hid}/claim", json={"operator_id": op.id})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["status"], HANDOFF_STATUS_IN_REVIEW)
        self.assertEqual(r1.json()["assigned_operator_id"], op.id)

        r_open = self.client.get("/internal/ops/handoffs/open")
        self.assertEqual(len(r_open.json()["items"]), 0)

        r2 = self.client.patch(f"/internal/ops/handoffs/{hid}/claim", json={})
        self.assertEqual(r2.status_code, 409)

        r3 = self.client.patch(f"/internal/ops/handoffs/{hid}/close", json={})
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["status"], HANDOFF_STATUS_CLOSED)

        r4 = self.client.patch(f"/internal/ops/handoffs/{hid}/close", json={})
        self.assertEqual(r4.status_code, 409)

    def test_invalid_operator_returns_400(self) -> None:
        user = self.create_user()
        h = Handoff(
            user_id=user.id,
            order_id=None,
            reason="x",
            priority="normal",
            status=HANDOFF_STATUS_OPEN,
            assigned_operator_id=None,
        )
        self.session.add(h)
        self.session.commit()
        hid = h.id
        r = self.client.patch(f"/internal/ops/handoffs/{hid}/claim", json={"operator_id": 999_999_999})
        self.assertEqual(r.status_code, 400)
