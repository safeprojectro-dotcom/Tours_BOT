"""Handoff entry persistence (Step 13) — minimal create path."""

from __future__ import annotations

import unittest

from app.models.handoff import Handoff
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

    def test_group_followup_start_creates_open_handoff(self) -> None:
        self.create_user(telegram_user_id=77_010)
        self.session.commit()
        svc = HandoffEntryService()
        hid = svc.create_for_group_followup_start(
            self.session,
            telegram_user_id=77_010,
        )
        self.assertIsNotNone(hid)
        row = self.session.get(Handoff, hid)
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.reason, HandoffEntryService.REASON_GROUP_FOLLOWUP_START)
        self.assertEqual(row.status, "open")
        self.session.commit()

    def test_group_followup_start_dedupes_open_handoff(self) -> None:
        self.create_user(telegram_user_id=77_005)
        self.session.commit()
        svc = HandoffEntryService()

        first = svc.create_for_group_followup_start(
            self.session,
            telegram_user_id=77_005,
        )
        self.assertIsNotNone(first)
        self.session.commit()

        second = svc.create_for_group_followup_start(
            self.session,
            telegram_user_id=77_005,
        )
        self.assertEqual(first, second)

    def test_group_followup_start_creates_new_after_previous_closed(self) -> None:
        self.create_user(telegram_user_id=77_006)
        self.session.commit()
        svc = HandoffEntryService()

        first = svc.create_for_group_followup_start(
            self.session,
            telegram_user_id=77_006,
        )
        self.assertIsNotNone(first)
        self.session.commit()

        first_row = self.session.get(Handoff, first)
        self.assertIsNotNone(first_row)
        assert first_row is not None
        first_row.status = "closed"
        self.session.commit()

        second = svc.create_for_group_followup_start(
            self.session,
            telegram_user_id=77_006,
        )
        self.assertIsNotNone(second)
        self.assertNotEqual(first, second)

    def test_should_show_group_followup_resolved_when_closed_no_open(self) -> None:
        user = self.create_user(telegram_user_id=77_020)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=None,
                reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                priority="normal",
                status="closed",
            )
        )
        self.session.commit()
        svc = HandoffEntryService()
        self.assertTrue(
            svc.should_show_group_followup_resolved_confirmation(self.session, user_id=user.id)
        )

    def test_should_show_group_followup_resolved_false_when_open(self) -> None:
        user = self.create_user(telegram_user_id=77_021)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=None,
                reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                priority="normal",
                status="open",
            )
        )
        self.session.commit()
        svc = HandoffEntryService()
        self.assertFalse(
            svc.should_show_group_followup_resolved_confirmation(self.session, user_id=user.id)
        )

    def test_should_show_group_followup_resolved_false_when_in_review(self) -> None:
        user = self.create_user(telegram_user_id=77_022)
        op = self.create_user(telegram_user_id=77_122)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=None,
                reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                priority="normal",
                status="in_review",
                assigned_operator_id=op.id,
            )
        )
        self.session.commit()
        svc = HandoffEntryService()
        self.assertFalse(
            svc.should_show_group_followup_resolved_confirmation(self.session, user_id=user.id)
        )

    def test_should_show_group_followup_resolved_false_when_only_other_reason(self) -> None:
        user = self.create_user(telegram_user_id=77_023)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=None,
                reason="private_contact",
                priority="normal",
                status="closed",
            )
        )
        self.session.commit()
        svc = HandoffEntryService()
        self.assertFalse(
            svc.should_show_group_followup_resolved_confirmation(self.session, user_id=user.id)
        )


if __name__ == "__main__":
    unittest.main()
