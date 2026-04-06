"""Phase 7 / Steps 3–4 — group gating + handoff-aware replies (service layer, no aiogram)."""

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

    def test_mention_triggers_default_ack_when_no_handoff_category(self) -> None:
        text = resolve_group_trigger_ack_reply(
            "Hey @tours_bot is this ok?",
            bot_username="tours_bot",
        )
        self.assertEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)
        self.assertLess(len(text or ""), 300)

    def test_approved_command_triggers_default_ack(self) -> None:
        text = resolve_group_trigger_ack_reply("/help", bot_username="tours_bot")
        self.assertEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_approved_trigger_phrase_triggers_default_ack_when_generic(self) -> None:
        text = resolve_group_trigger_ack_reply("How much is the trip?", bot_username="tours_bot")
        self.assertEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_discount_request_uses_category_reply(self) -> None:
        text = resolve_group_trigger_ack_reply(
            "@tours_bot Is there any discount for families?",
            bot_username="tours_bot",
        )
        self.assertIsNotNone(text)
        self.assertIn("discount", text.lower())
        self.assertNotEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_group_booking_uses_category_reply(self) -> None:
        text = resolve_group_trigger_ack_reply(
            "@tours_bot We are 10 people, can you fit us?",
            bot_username="tours_bot",
        )
        self.assertIsNotNone(text)
        self.assertIn("group", text.lower())
        self.assertNotEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_complaint_uses_category_reply(self) -> None:
        text = resolve_group_trigger_ack_reply(
            "@tours_bot This is unacceptable, I want a refund",
            bot_username="tours_bot",
        )
        self.assertIsNotNone(text)
        self.assertIn("private", text.lower())
        self.assertNotEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_explicit_human_request_uses_category_reply(self) -> None:
        text = resolve_group_trigger_ack_reply(
            "@tours_bot I need to speak to an operator please",
            bot_username="tours_bot",
        )
        self.assertIsNotNone(text)
        self.assertIn("human", text.lower())
        self.assertNotEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_unclear_payment_issue_uses_category_reply(self) -> None:
        text = resolve_group_trigger_ack_reply(
            "@tours_bot I paid but the app still shows unpaid",
            bot_username="tours_bot",
        )
        self.assertIsNotNone(text)
        self.assertIn("payment", text.lower())
        self.assertNotEqual(text, GROUP_TRIGGER_ACK_REPLY_TEXT)

    def test_ack_is_short_and_safe_placeholder(self) -> None:
        self.assertIn("private", GROUP_TRIGGER_ACK_REPLY_TEXT.lower())
        self.assertIn("mini app", GROUP_TRIGGER_ACK_REPLY_TEXT.lower())


if __name__ == "__main__":
    unittest.main()
