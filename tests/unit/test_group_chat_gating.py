"""Phase 7 / Step 3 — group gating ack (service layer, no aiogram)."""

import unittest

from app.services.group_chat_gating import (
    GROUP_TRIGGER_ACK_REPLY_TEXT,
    resolve_group_trigger_ack_reply,
)


class TestGroupChatGating(unittest.TestCase):
    def test_no_bot_username_stays_silent(self) -> None:
        self.assertIsNone(
            resolve_group_trigger_ack_reply("Hello @mybot", bot_username=None),
        )

    def test_non_trigger_message_stays_silent(self) -> None:
        self.assertIsNone(
            resolve_group_trigger_ack_reply("random chat lol", bot_username="tours_bot"),
        )

    def test_mention_triggers_short_ack(self) -> None:
        text = resolve_group_trigger_ack_reply(
            "Hey @tours_bot is this ok?",
            bot_username="tours_bot",
        )
        self.assertEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)
        self.assertLess(len(text or ""), 300)

    def test_approved_command_triggers_ack(self) -> None:
        text = resolve_group_trigger_ack_reply("/help", bot_username="tours_bot")
        self.assertEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_approved_trigger_phrase_triggers_ack(self) -> None:
        text = resolve_group_trigger_ack_reply("How much is the trip?", bot_username="tours_bot")
        self.assertEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_ack_is_short_and_safe_placeholder(self) -> None:
        self.assertIn("private", GROUP_TRIGGER_ACK_REPLY_TEXT.lower())
        self.assertIn("mini app", GROUP_TRIGGER_ACK_REPLY_TEXT.lower())


if __name__ == "__main__":
    unittest.main()
