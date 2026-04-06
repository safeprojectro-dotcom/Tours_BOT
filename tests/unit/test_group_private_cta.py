"""Phase 7 / Steps 5–6 — private CTA deep links + ``/start`` payload matching (no aiogram)."""

import unittest

from app.schemas.group_assistant_triggers import HandoffCategory, HandoffTriggerResult
from app.schemas.group_private_cta import GroupPrivateEntryMode
from app.services.group_private_cta import (
    START_PAYLOAD_GRP_FOLLOWUP,
    START_PAYLOAD_GRP_PRIVATE,
    build_group_private_cta_target,
    entry_mode_from_handoff,
    match_group_cta_start_payload,
)


class TestGroupPrivateCta(unittest.TestCase):
    def test_generic_deep_link_and_payload(self) -> None:
        t = build_group_private_cta_target(
            bot_username="tours_bot",
            entry_mode=GroupPrivateEntryMode.GENERIC_PRIVATE,
        )
        self.assertEqual(t.entry_mode, GroupPrivateEntryMode.GENERIC_PRIVATE)
        self.assertEqual(t.start_payload, START_PAYLOAD_GRP_PRIVATE)
        self.assertEqual(t.deep_link, "https://t.me/tours_bot?start=grp_private")

    def test_human_followup_deep_link_and_payload(self) -> None:
        t = build_group_private_cta_target(
            bot_username="@tours_bot",
            entry_mode=GroupPrivateEntryMode.HUMAN_FOLLOWUP,
        )
        self.assertEqual(t.start_payload, START_PAYLOAD_GRP_FOLLOWUP)
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

    def test_match_grp_private_and_whitespace(self) -> None:
        self.assertEqual(match_group_cta_start_payload(" grp_private "), START_PAYLOAD_GRP_PRIVATE)

    def test_match_grp_followup(self) -> None:
        self.assertEqual(match_group_cta_start_payload("grp_followup"), START_PAYLOAD_GRP_FOLLOWUP)

    def test_grp_private_payload_distinct_from_followup_for_handoff_gate(self) -> None:
        """Step 7 persistence is keyed on ``grp_followup`` only; ``grp_private`` must remain distinct."""
        self.assertEqual(match_group_cta_start_payload("grp_private"), START_PAYLOAD_GRP_PRIVATE)
        self.assertNotEqual(
            match_group_cta_start_payload("grp_private"),
            match_group_cta_start_payload("grp_followup"),
        )

    def test_match_none_for_tour_payload(self) -> None:
        self.assertIsNone(match_group_cta_start_payload("tour_BELGRADE-1"))

    def test_match_none_for_empty(self) -> None:
        self.assertIsNone(match_group_cta_start_payload(None))
        self.assertIsNone(match_group_cta_start_payload(""))


if __name__ == "__main__":
    unittest.main()
