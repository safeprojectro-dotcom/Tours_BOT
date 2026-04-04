"""Waitlist ops claim/close (Phase 5 Step 17)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.api.ops_queue_auth import require_ops_queue_token
from app.db.session import get_db
from app.main import create_app
from app.models.enums import TourStatus
from app.models.waitlist import WaitlistEntry
from app.services.waitlist_ops_actions import (
    WAITLIST_STATUS_ACTIVE,
    WAITLIST_STATUS_CLOSED,
    WAITLIST_STATUS_IN_REVIEW,
    WaitlistOpsActionService,
)
from tests.unit.base import FoundationDBTestCase


class WaitlistOpsActionServiceTests(FoundationDBTestCase):
    def test_claim_then_conflict(self) -> None:
        user = self.create_user()
        tour = self.create_tour(code="WL-SVC")
        w = WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=2, status=WAITLIST_STATUS_ACTIVE)
        self.session.add(w)
        self.session.commit()

        svc = WaitlistOpsActionService()
        row = svc.claim(self.session, waitlist_entry_id=w.id)
        self.assertEqual(row.status, WAITLIST_STATUS_IN_REVIEW)

        from app.services.waitlist_ops_actions import WaitlistClaimStateError

        with self.assertRaises(WaitlistClaimStateError) as ctx:
            svc.claim(self.session, waitlist_entry_id=w.id)
        self.assertEqual(ctx.exception.current_status, WAITLIST_STATUS_IN_REVIEW)

    def test_close_from_active_and_double_close(self) -> None:
        user = self.create_user()
        tour = self.create_tour(code="WL-CL")
        w = WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=1, status=WAITLIST_STATUS_ACTIVE)
        self.session.add(w)
        self.session.commit()

        svc = WaitlistOpsActionService()
        closed = svc.close(self.session, waitlist_entry_id=w.id)
        self.assertEqual(closed.status, WAITLIST_STATUS_CLOSED)

        from app.services.waitlist_ops_actions import WaitlistCloseStateError

        with self.assertRaises(WaitlistCloseStateError):
            svc.close(self.session, waitlist_entry_id=w.id)


class WaitlistOpsAPITests(FoundationDBTestCase):
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

    def test_claim_close_flow_and_active_queue(self) -> None:
        user = self.create_user()
        tour = self.create_tour(
            code="WL-API",
            title_default="Wl Api",
            departure_datetime=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
            return_datetime=datetime(2026, 7, 2, 20, 0, tzinfo=UTC),
            status=TourStatus.OPEN_FOR_SALE,
        )
        w = WaitlistEntry(user_id=user.id, tour_id=tour.id, seats_count=2, status=WAITLIST_STATUS_ACTIVE)
        self.session.add(w)
        self.session.commit()
        wid = w.id

        r0 = self.client.get("/internal/ops/waitlist/active")
        self.assertEqual(len(r0.json()["items"]), 1)

        r1 = self.client.patch(f"/internal/ops/waitlist/{wid}/claim")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["status"], WAITLIST_STATUS_IN_REVIEW)

        r_active = self.client.get("/internal/ops/waitlist/active")
        self.assertEqual(len(r_active.json()["items"]), 0)

        r2 = self.client.patch(f"/internal/ops/waitlist/{wid}/claim")
        self.assertEqual(r2.status_code, 409)

        r3 = self.client.patch(f"/internal/ops/waitlist/{wid}/close")
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["status"], WAITLIST_STATUS_CLOSED)

        r4 = self.client.patch(f"/internal/ops/waitlist/{wid}/close")
        self.assertEqual(r4.status_code, 409)
        self.assertEqual(r4.json()["detail"]["code"], "waitlist_already_closed")
