"""Phase 7 / Step 6 — translation keys for group CTA private /start intros."""

import unittest

from app.bot.messages import translate


class TestPrivateStartGrpMessages(unittest.TestCase):
    def test_intro_keys_exist_for_en(self) -> None:
        a = translate("en", "start_grp_private_intro")
        b = translate("en", "start_grp_followup_intro")
        self.assertTrue(len(a) > 10)
        self.assertTrue(len(b) > 10)
        self.assertIn("/contact", b)


if __name__ == "__main__":
    unittest.main()
