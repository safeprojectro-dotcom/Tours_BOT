"""B15C2: queue pin helper used after supplier-offer Telegram admin mutations."""

from __future__ import annotations

import unittest

from app.bot.handlers.admin_moderation import _queue_state_after_offer_mutation


class QueueStateAfterOfferMutationTests(unittest.TestCase):
    def test_offer_still_in_fresh_queue_preserves_index(self) -> None:
        q, idx, cur = _queue_state_after_offer_mutation(fresh_queue_ids=[10, 20, 30], offer_id=20)
        self.assertEqual(q, [10, 20, 30])
        self.assertEqual(idx, 1)
        self.assertEqual(cur, 20)

    def test_offer_not_in_fresh_queue_pins_singleton(self) -> None:
        q, idx, cur = _queue_state_after_offer_mutation(fresh_queue_ids=[10, 30], offer_id=20)
        self.assertEqual(q, [20])
        self.assertEqual(idx, 0)
        self.assertEqual(cur, 20)

    def test_empty_fresh_queue_pins_singleton(self) -> None:
        q, idx, cur = _queue_state_after_offer_mutation(fresh_queue_ids=[], offer_id=7)
        self.assertEqual(q, [7])
        self.assertEqual(idx, 0)
        self.assertEqual(cur, 7)


if __name__ == "__main__":
    unittest.main()
