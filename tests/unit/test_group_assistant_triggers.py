"""Phase 7 / Step 2 — group + handoff trigger evaluation helpers."""

import unittest

from app.schemas.group_assistant_triggers import (
    GroupTriggerReason,
    HandoffCategory,
)
from app.services.assistant_trigger_evaluation import evaluate_assistant_trigger_snapshot
from app.services.group_trigger_evaluation import evaluate_group_trigger
from app.services.handoff_trigger_evaluation import evaluate_handoff_triggers


class TestGroupTriggerEvaluation(unittest.TestCase):
    def test_mention(self) -> None:
        r = evaluate_group_trigger("Hi @tours_bot what is the price?", bot_username="tours_bot")
        self.assertTrue(r.should_respond_in_group)
        self.assertEqual(r.group_trigger_reason, GroupTriggerReason.MENTION)

    def test_approved_command(self) -> None:
        r = evaluate_group_trigger("/help", bot_username="tours_bot")
        self.assertTrue(r.should_respond_in_group)
        self.assertEqual(r.group_trigger_reason, GroupTriggerReason.APPROVED_COMMAND)

    def test_command_with_bot_suffix_stripped(self) -> None:
        r = evaluate_group_trigger("/tours@ToursBot", bot_username="toursbot")
        self.assertTrue(r.should_respond_in_group)
        self.assertEqual(r.group_trigger_reason, GroupTriggerReason.APPROVED_COMMAND)

    def test_approved_trigger_phrase(self) -> None:
        r = evaluate_group_trigger("How much is the Belgrade trip?", bot_username="x")
        self.assertTrue(r.should_respond_in_group)
        self.assertEqual(r.group_trigger_reason, GroupTriggerReason.APPROVED_TRIGGER_PHRASE)

    def test_non_trigger_random_chat(self) -> None:
        r = evaluate_group_trigger("lol ok", bot_username="tours_bot")
        self.assertFalse(r.should_respond_in_group)
        self.assertEqual(r.group_trigger_reason, GroupTriggerReason.NONE)

    def test_empty_message(self) -> None:
        r = evaluate_group_trigger("   ", bot_username="tours_bot")
        self.assertFalse(r.should_respond_in_group)


class TestHandoffTriggerEvaluation(unittest.TestCase):
    def test_discount(self) -> None:
        r = evaluate_handoff_triggers("Is there any discount for families?")
        self.assertTrue(r.handoff_required)
        self.assertEqual(r.handoff_category, HandoffCategory.DISCOUNT_REQUEST)

    def test_group_booking(self) -> None:
        r = evaluate_handoff_triggers("We are 10 people, can you fit us on one bus?")
        self.assertTrue(r.handoff_required)
        self.assertEqual(r.handoff_category, HandoffCategory.GROUP_BOOKING)

    def test_custom_pickup(self) -> None:
        r = evaluate_handoff_triggers("Can you pick up from a different city?")
        self.assertTrue(r.handoff_required)
        self.assertEqual(r.handoff_category, HandoffCategory.CUSTOM_PICKUP)

    def test_complaint(self) -> None:
        r = evaluate_handoff_triggers("This is unacceptable, I want a refund")
        self.assertTrue(r.handoff_required)
        self.assertEqual(r.handoff_category, HandoffCategory.COMPLAINT)

    def test_unclear_payment_issue(self) -> None:
        r = evaluate_handoff_triggers("I paid but the app still shows unpaid")
        self.assertTrue(r.handoff_required)
        self.assertEqual(r.handoff_category, HandoffCategory.UNCLEAR_PAYMENT_ISSUE)

    def test_explicit_human_request(self) -> None:
        r = evaluate_handoff_triggers("I need to speak to an operator please")
        self.assertTrue(r.handoff_required)
        self.assertEqual(r.handoff_category, HandoffCategory.EXPLICIT_HUMAN_REQUEST)

    def test_low_confidence_only_when_signaled(self) -> None:
        r_plain = evaluate_handoff_triggers("What is the weather in Paris?")
        self.assertFalse(r_plain.handoff_required)
        r_flag = evaluate_handoff_triggers("What is the weather in Paris?", low_confidence_signal=True)
        self.assertTrue(r_flag.handoff_required)
        self.assertEqual(r_flag.handoff_category, HandoffCategory.LOW_CONFIDENCE_ANSWER)


class TestAssistantTriggerSnapshot(unittest.TestCase):
    def test_snapshot_composes(self) -> None:
        snap = evaluate_assistant_trigger_snapshot(
            "/help I need to speak to an operator",
            bot_username="tours_bot",
        )
        self.assertTrue(snap.should_respond_in_group)
        self.assertEqual(snap.group_trigger_reason, GroupTriggerReason.APPROVED_COMMAND)
        self.assertTrue(snap.handoff_required)
        self.assertEqual(snap.handoff_category, HandoffCategory.EXPLICIT_HUMAN_REQUEST)


if __name__ == "__main__":
    unittest.main()
