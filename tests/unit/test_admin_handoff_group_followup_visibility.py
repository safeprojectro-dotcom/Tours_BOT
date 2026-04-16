"""Phase 7 / Step 9 — read-only visibility helpers for group_followup_start (admin handoff surfaces)."""

from __future__ import annotations

import unittest

from app.services.admin_handoff_queue import compute_group_followup_visibility
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


if __name__ == "__main__":
    unittest.main()
