import os
import random
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game


class BarrelDescentTests(unittest.TestCase):
    def barrel_at_ladder(self):
        barrel = game.Barrel()
        barrel.pos.x = game.LADDERS[3][0]
        return barrel

    def test_thirty_percent_boundary(self):
        for roll, expected in [(0.0, 3), (0.2999, 3), (0.3, None), (0.6999, None), (0.9999, None)]:
            with self.subTest(roll=roll), patch("game.random.random", return_value=roll):
                barrel = self.barrel_at_ladder()
                barrel.update(0)
                self.assertEqual(barrel.ladder, expected)

    def test_rejected_ladder_is_not_retried_next_frame(self):
        barrel = self.barrel_at_ladder()
        with patch("game.random.random", return_value=0.5) as roll:
            for _ in range(10):
                barrel.update(0)
        self.assertEqual(roll.call_count, 1)
        self.assertIsNone(barrel.ladder)

    def test_seeded_population_descends_about_thirty_percent(self):
        rng = random.Random(42)
        descended = 0
        with patch("game.random.random", side_effect=rng.random):
            for _ in range(10000):
                barrel = self.barrel_at_ladder()
                barrel.update(0)
                descended += barrel.ladder is not None
        self.assertTrue(2800 <= descended <= 3200, descended)


if __name__ == "__main__":
    unittest.main()
