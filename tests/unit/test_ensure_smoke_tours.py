"""Unit tests for smoke tour schedule helper (no DB)."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from app.scripts.ensure_smoke_tours import compute_smoke_tour_schedule


class ComputeSmokeTourScheduleTests(unittest.TestCase):
    def test_ordering_and_future(self) -> None:
        now = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
        dep, ret, deadline = compute_smoke_tour_schedule(now=now, days_ahead=60, duration_days=2)
        self.assertGreater(dep, now)
        self.assertGreater(ret, dep)
        self.assertGreater(deadline, now)
        self.assertLess(deadline, dep)
        self.assertEqual(dep.hour, 8)
        self.assertEqual(dep.minute, 0)

    def test_days_ahead_too_small_rejected(self) -> None:
        now = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
        with self.assertRaises(ValueError):
            compute_smoke_tour_schedule(now=now, days_ahead=1)


if __name__ == "__main__":
    unittest.main()
