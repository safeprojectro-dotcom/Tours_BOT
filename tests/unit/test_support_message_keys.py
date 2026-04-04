"""Ensure new support/handoff bot strings exist (Step 13)."""

from __future__ import annotations

import unittest

from app.bot.messages import translate


class SupportMessageKeysTests(unittest.TestCase):
    def test_handoff_and_human_strings_resolve(self) -> None:
        translate("en", "human_command_reply")
        translate("ro", "human_command_reply")
        translate("en", "handoff_request_recorded", ref="99")
        translate("ro", "handoff_request_recorded", ref="99")
        translate("en", "help_command_reply")
        translate("ro", "contact_command_reply")


if __name__ == "__main__":
    unittest.main()
