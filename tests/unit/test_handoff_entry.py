"""Handoff entry persistence (Step 13) — minimal create path."""

from __future__ import annotations

import unittest

from app.services.handoff_entry import HandoffEntryService
from tests.unit.base import FoundationDBTestCase


class HandoffEntryServiceTests(FoundationDBTestCase):
    def test_create_handoff_for_telegram_user(self) -> None:
        user = self.create_user(telegram_user_id=77_001)
        self.session.commit()
        svc = HandoffEntryService()
        hid = svc.create_for_telegram_user(
            self.session,
            telegram_user_id=77_001,
            reason="test_reason",
        )
        self.assertIsNotNone(hid)
        self.session.commit()

    def test_create_handoff_rejects_foreign_order(self) -> None:
        u1 = self.create_user(telegram_user_id=77_002)
        u2 = self.create_user(telegram_user_id=77_003)
        tour = self.create_tour()
        bp = self.create_boarding_point(tour)
        order = self.create_order(u2, tour, bp)
        self.session.commit()

        svc = HandoffEntryService()
        hid = svc.create_for_telegram_user(
            self.session,
            telegram_user_id=77_002,
            reason="should_fail",
            order_id=order.id,
        )
        self.assertIsNone(hid)

    def test_create_handoff_with_owned_order(self) -> None:
        user = self.create_user(telegram_user_id=77_004)
        tour = self.create_tour()
        bp = self.create_boarding_point(tour)
        order = self.create_order(user, tour, bp)
        self.session.commit()

        svc = HandoffEntryService()
        hid = svc.create_for_telegram_user(
            self.session,
            telegram_user_id=77_004,
            reason="with_order",
            order_id=order.id,
        )
        self.assertIsNotNone(hid)


if __name__ == "__main__":
    unittest.main()
