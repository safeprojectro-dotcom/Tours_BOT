"""Phase 7 follow-up UX consolidation: private intro keys vs admin read-side buckets (no new workflow)."""

from __future__ import annotations

import unittest

from app.models.handoff import Handoff
from app.services.admin_handoff_queue import compute_group_followup_queue_state
from app.services.handoff_entry import HandoffEntryService
from tests.unit.base import FoundationDBTestCase


class GroupFollowupPrivateAdminAlignmentTests(FoundationDBTestCase):
    """Private ``group_followup_private_intro_key`` aligns with ``group_followup_queue_state`` buckets."""

    def _bucket(
        self,
        *,
        status: str,
        assigned_operator_id: int | None,
    ) -> str | None:
        return compute_group_followup_queue_state(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            status=status,
            assigned_operator_id=assigned_operator_id,
        )

    def test_open_unassigned_pending_matches_awaiting_assignment(self) -> None:
        user = self.create_user(telegram_user_id=99_101)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=None,
                reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                priority="normal",
                status="open",
                assigned_operator_id=None,
            )
        )
        self.session.commit()
        svc = HandoffEntryService()
        self.assertEqual(
            svc.group_followup_private_intro_key(self.session, user_id=user.id),
            "start_grp_followup_readiness_pending",
        )
        self.assertEqual(self._bucket(status="open", assigned_operator_id=None), "awaiting_assignment")

    def test_open_assigned_matches_assigned_open(self) -> None:
        user = self.create_user(telegram_user_id=99_102)
        op = self.create_user(telegram_user_id=99_202)
        self.session.add(
            Handoff(
                user_id=user.id,
                order_id=None,
                reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
                priority="normal",
                status="open",
                assigned_operator_id=op.id,
            )
        )
        self.session.commit()
        svc = HandoffEntryService()
        self.assertEqual(
            svc.group_followup_private_intro_key(self.session, user_id=user.id),
            "start_grp_followup_readiness_assigned",
        )
        self.assertEqual(self._bucket(status="open", assigned_operator_id=op.id), "assigned_open")

    def test_in_review_matches_in_work_bucket(self) -> None:
        user = self.create_user(telegram_user_id=99_103)
        op = self.create_user(telegram_user_id=99_203)
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
        self.assertEqual(
            svc.group_followup_private_intro_key(self.session, user_id=user.id),
            "start_grp_followup_readiness_in_progress",
        )
        self.assertEqual(self._bucket(status="in_review", assigned_operator_id=op.id), "in_work")

    def test_closed_no_open_matches_resolved_bucket(self) -> None:
        user = self.create_user(telegram_user_id=99_104)
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
        self.assertEqual(
            svc.group_followup_private_intro_key(self.session, user_id=user.id),
            "start_grp_followup_resolved_intro",
        )
        self.assertEqual(self._bucket(status="closed", assigned_operator_id=None), "resolved")


if __name__ == "__main__":
    unittest.main()
