"""Hotfix: custom request submit UX strings and guard (no Flet runtime)."""

from __future__ import annotations

import unittest

from mini_app.ui_strings import shell


class CustomRequestSubmitHotfixTests(unittest.TestCase):
    def test_romanian_success_and_busy_keys_exist(self) -> None:
        self.assertTrue(len(shell("ro", "custom_request_submit_sending")) > 0)
        self.assertTrue(len(shell("ro", "custom_request_success_cta_my_requests")) > 0)
        self.assertTrue(len(shell("ro", "custom_request_success_back_catalog")) > 0)
        self.assertTrue(len(shell("ro", "custom_request_success_new_request")) > 0)

    def test_english_hotfix_keys_exist(self) -> None:
        self.assertIn("Sending", shell("en", "custom_request_submit_sending"))

    def test_bridge_404_waiting_state_copy_exists(self) -> None:
        self.assertIn("No booking step is available yet", shell("en", "rfq_bridge_no_step_yet"))
        self.assertTrue(len(shell("ro", "rfq_bridge_no_step_yet")) > 0)


if __name__ == "__main__":
    unittest.main()
