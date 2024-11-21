from datetime import datetime, timezone
import unittest

from utils.scheduling import next_force_wipe, roll_forward


class SchedulingTests(unittest.TestCase):
    def test_next_force_wipe_moves_to_the_following_thursday_after_wipe_time(self):
        now = datetime(2026, 10, 1, 19, 1, tzinfo=timezone.utc)

        result = datetime.fromtimestamp(next_force_wipe(now), tz=timezone.utc)

        self.assertEqual(result.weekday(), 3)
        self.assertEqual(result.hour, 18)  # 19:00 BST is 18:00 UTC.
        self.assertEqual(result.date().isoformat(), "2026-10-08")

    def test_roll_forward_catches_up_multiple_missed_intervals(self):
        self.assertEqual(roll_forward(100, 10, now=135), 140)

    def test_roll_forward_rejects_invalid_intervals(self):
        with self.assertRaises(ValueError):
            roll_forward(100, 0, now=0)
