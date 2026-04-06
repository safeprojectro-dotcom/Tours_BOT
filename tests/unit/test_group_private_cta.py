"""Phase 7 / Step 5 — private CTA / deep-link helper (no aiogram)."""

import unittest

from app.schemas.group_assistant_triggers import HandoffCategory, HandoffTriggerResult
from app.schemas.group_private_cta import GroupPrivateEntryMode
from app.services.group_private_cta import build_group_private_cta_target, entry_mode_from_handoff


class TestGroupPrivateCta(unittest.TestCase):
    def test_generic_deep_link_and_payload(self) -> None:
        t = build_group_private_cta_target(
            bot_username="tours_bot",
            entry_mode=GroupPrivateEntryMode.GENERIC_PRIVATE,
        )
        self.assertEqual(t.entry_mode, GroupPrivateEntryMode.GENERIC_PRIVATE)
        self.assertEqual(t.start_payload, "grp_private")
        self.assertEqual(t.deep_link, "https://t.me/tours_bot?start=grp_private")

    def test_human_followup_deep_link_and_payload(self) -> None:
        t = build_group_private_cta_target(
            bot_username="@tours_bot",
            entry_mode=GroupPrivateEntryMode.HUMAN_FOLLOWUP,
        )
        self.assertEqual(t.start_payload, "grp_followup")
        self.assertEqual(t.deep_link, "https://t.me/tours_bot?start=grp_followup")

    def test_entry_mode_from_handoff_generic(self) -> None:
        h = HandoffTriggerResult(handoff_required=False, handoff_category=None)
        self.assertEqual(entry_mode_from_handoff(h), GroupPrivateEntryMode.GENERIC_PRIVATE)

    def test_entry_mode_from_handoff_human(self) -> None:
        h = HandoffTriggerResult(
            handoff_required=True,
            handoff_category=HandoffCategory.DISCOUNT_REQUEST,
        )
        self.assertEqual(entry_mode_from_handoff(h), GroupPrivateEntryMode.HUMAN_FOLLOWUP)

    def test_empty_bot_username_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_group_private_cta_target(
                bot_username="   ",
                entry_mode=GroupPrivateEntryMode.GENERIC_PRIVATE,
            )


if __name__ == "__main__":
    unittest.main()
