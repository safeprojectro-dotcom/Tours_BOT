"""Phase 7 / Steps 3–5 — group gating + handoff-aware replies + private CTA link (service layer)."""

import unittest

from app.schemas.group_private_cta import GroupPrivateEntryMode
from app.services.group_chat_gating import (
    GROUP_TRIGGER_ACK_REPLY_TEXT,
    resolve_group_trigger_ack_reply,
)
from app.services.group_private_cta import build_group_private_cta_target


class TestGroupChatGating(unittest.TestCase):
    def _expected_with_cta(self, base: str, *, mode: GroupPrivateEntryMode) -> str:
        cta = build_group_private_cta_target(bot_username="tours_bot", entry_mode=mode)
        return f"{base} — {cta.deep_link}"

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
        self.assertEqual(
            text,
            self._expected_with_cta(GROUP_TRIGGER_ACK_REPLY_TEXT, mode=GroupPrivateEntryMode.GENERIC_PRIVATE),
        )
        self.assertIn("https://t.me/tours_bot?start=grp_private", text or "")
        self.assertLess(len(text or ""), 500)

    def test_approved_command_triggers_default_ack(self) -> None:
        text = resolve_group_trigger_ack_reply("/help", bot_username="tours_bot")
        self.assertEqual(
            text,
            self._expected_with_cta(GROUP_TRIGGER_ACK_REPLY_TEXT, mode=GroupPrivateEntryMode.GENERIC_PRIVATE),
        )

    def test_approved_trigger_phrase_triggers_default_ack_when_generic(self) -> None:
        text = resolve_group_trigger_ack_reply("How much is the trip?", bot_username="tours_bot")
        self.assertEqual(
            text,
            self._expected_with_cta(GROUP_TRIGGER_ACK_REPLY_TEXT, mode=GroupPrivateEntryMode.GENERIC_PRIVATE),
        )

    def test_discount_request_uses_category_reply(self) -> None:
        text = resolve_group_trigger_ack_reply(
            "@tours_bot Is there any discount for families?",
            bot_username="tours_bot",
        )
        self.assertIsNotNone(text)
        self.assertIn("discount", text.lower())
        self.assertIn("https://t.me/tours_bot?start=grp_followup", text or "")
        self.assertNotEqual(
            text,
            self._expected_with_cta(GROUP_TRIGGER_ACK_REPLY_TEXT, mode=GroupPrivateEntryMode.GENERIC_PRIVATE),
        )

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
