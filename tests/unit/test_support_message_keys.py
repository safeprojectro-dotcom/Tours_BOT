"""Ensure new support/handoff bot strings exist (Step 13)."""

from __future__ import annotations

import unittest

from app.bot.messages import translate
from mini_app.ui_strings import shell


class SupportMessageKeysTests(unittest.TestCase):
    def test_handoff_and_human_strings_resolve(self) -> None:
        for lang in ("en", "ro", "ru", "sr", "hu", "it", "de"):
            translate(lang, "contact_command_reply")
            translate(lang, "human_command_reply")
            translate(lang, "handoff_request_recorded", ref="99")
            translate(lang, "handoff_request_failed")
        translate("en", "help_command_reply")

    def test_mini_app_support_shell_keys(self) -> None:
        for lang in ("en", "ro", "ru", "sr", "hu", "it", "de"):
            shell(lang, "support_banner_title")
            shell(lang, "support_banner_body")
            shell(lang, "support_cta_log_request")
            shell(lang, "booking_support_body")
            shell(lang, "payment_support_body")
            shell(lang, "support_request_success", ref="1")
            shell(lang, "support_request_error")


if __name__ == "__main__":
    unittest.main()
