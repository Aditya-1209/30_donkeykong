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


class ThemeTests(unittest.TestCase):
    def test_theme_starts_at_default_and_clamps(self):
        self.assertEqual(game.theme_color(0), game.BG)
        self.assertEqual(game.theme_color(-100), game.BG)
        self.assertEqual(game.theme_color(1000), (65, 25, 40))
        self.assertEqual(game.theme_color(100000), game.theme_color(1000))

    def test_theme_warms_gradually_with_valid_rgb_channels(self):
        previous = game.theme_color(0)
        for score in range(0, 1100, 100):
            color = game.theme_color(score)
            self.assertEqual(len(color), 3)
            self.assertTrue(all(isinstance(channel, int) and 0 <= channel <= 255 for channel in color))
            self.assertGreaterEqual(color[0], previous[0])
            previous = color
        self.assertNotEqual(game.theme_color(100), game.BG)


if __name__ == "__main__":
    unittest.main()
