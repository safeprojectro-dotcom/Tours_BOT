"""Phase 7 / Steps 9–11 + 13–14 — read-only visibility helpers for group_followup_start (admin handoff surfaces)."""

from __future__ import annotations

import unittest

from app.services.admin_handoff_queue import (
    compute_group_followup_assignment_visibility,
    compute_group_followup_queue_state,
    compute_group_followup_resolution_label,
    compute_group_followup_visibility,
)
from app.services.handoff_entry import HandoffEntryService


class ComputeGroupFollowupVisibilityTests(unittest.TestCase):
    def test_group_followup_start_reason_is_visible(self) -> None:
        is_gf, label = compute_group_followup_visibility(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
        )
        self.assertTrue(is_gf)
        self.assertIsNotNone(label)
        self.assertIn("grp_followup", label)

    def test_other_reason_not_flagged(self) -> None:
        is_gf, label = compute_group_followup_visibility(reason="private_contact")
        self.assertFalse(is_gf)
        self.assertIsNone(label)


class ComputeGroupFollowupAssignmentVisibilityTests(unittest.TestCase):
    """Phase 7 / Step 11 — assigned group_followup_start read-side triage flags."""

    def test_unassigned_group_followup_no_assigned_flag(self) -> None:
        is_agf, work = compute_group_followup_assignment_visibility(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            assigned_operator_id=None,
            status="open",
        )
        self.assertFalse(is_agf)
        self.assertIsNotNone(work)
        self.assertIn("Queued", work)

    def test_assigned_open_group_followup(self) -> None:
        is_agf, work = compute_group_followup_assignment_visibility(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            assigned_operator_id=42,
            status="open",
        )
        self.assertTrue(is_agf)
        self.assertIn("Assigned", work or "")
        self.assertIn("follow-up", work or "")

    def test_assigned_in_review_group_followup(self) -> None:
        is_agf, work = compute_group_followup_assignment_visibility(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            assigned_operator_id=1,
            status="in_review",
        )
        self.assertTrue(is_agf)
        self.assertIn("progress", work or "")

    def test_assigned_closed_group_followup(self) -> None:
        is_agf, work = compute_group_followup_assignment_visibility(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            assigned_operator_id=1,
            status="closed",
        )
        self.assertTrue(is_agf)
        self.assertIn("closed", work or "")

    def test_other_reason_with_operator_not_assigned_group_followup(self) -> None:
        is_agf, work = compute_group_followup_assignment_visibility(
            reason="private_contact",
            assigned_operator_id=99,
            status="open",
        )
        self.assertFalse(is_agf)
        self.assertIsNone(work)


class ComputeGroupFollowupQueueStateTests(unittest.TestCase):
    """Phase 7 / Step 15 — single queue bucket for group_followup_start (read-only)."""

    def test_resolved_when_closed_group_followup(self) -> None:
        s = compute_group_followup_queue_state(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            status="closed",
            assigned_operator_id=1,
        )
        self.assertEqual(s, "resolved")

    def test_in_work_when_in_review(self) -> None:
        s = compute_group_followup_queue_state(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            status="in_review",
            assigned_operator_id=1,
        )
        self.assertEqual(s, "in_work")

    def test_awaiting_assignment_open_unassigned(self) -> None:
        s = compute_group_followup_queue_state(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            status="open",
            assigned_operator_id=None,
        )
        self.assertEqual(s, "awaiting_assignment")

    def test_assigned_open(self) -> None:
        s = compute_group_followup_queue_state(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            status="open",
            assigned_operator_id=99,
        )
        self.assertEqual(s, "assigned_open")

    def test_private_contact_none(self) -> None:
        self.assertIsNone(
            compute_group_followup_queue_state(
                reason="private_contact",
                status="closed",
                assigned_operator_id=1,
            )
        )


class ComputeGroupFollowupResolutionLabelTests(unittest.TestCase):
    """Phase 7 / Steps 13–14 — closed group_followup_start resolution read label."""

    def test_closed_group_followup_has_resolution_label(self) -> None:
        lbl = compute_group_followup_resolution_label(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            status="closed",
        )
        self.assertIsNotNone(lbl)
        self.assertIn("resolved", lbl.lower())

    def test_open_group_followup_no_resolution_label(self) -> None:
        lbl = compute_group_followup_resolution_label(
            reason=HandoffEntryService.REASON_GROUP_FOLLOWUP_START,
            status="open",
        )
        self.assertIsNone(lbl)

    def test_other_reason_closed_no_resolution_label(self) -> None:
        lbl = compute_group_followup_resolution_label(reason="private_contact", status="closed")
        self.assertIsNone(lbl)


if __name__ == "__main__":
    unittest.main()
