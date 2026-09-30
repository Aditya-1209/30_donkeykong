import os
import random
import unittest
from types import SimpleNamespace
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


class BonusEffectTests(unittest.TestCase):
    def test_hook_uses_awarded_points_and_copies_barrel_position(self):
        player, barrel = game.Player(), game.Barrel()
        barrel.bonus_points = 200
        game.on_barrel_jumped(player, barrel)
        self.assertEqual(len(player.bonus_labels), 1)
        label = player.bonus_labels[0]
        self.assertEqual(label.points, 200)
        original = label.pos.copy()
        barrel.pos.x += 100
        self.assertEqual(label.pos, original)

    def test_effect_floats_and_expires_after_one_second(self):
        player, barrel = game.Player(), game.Barrel()
        game.on_barrel_jumped(player, barrel)
        original_y = player.bonus_labels[0].pos.y
        player.update_effects(0.5)
        self.assertLess(player.bonus_labels[0].pos.y, original_y)
        self.assertAlmostEqual(player.bonus_labels[0].remaining, 0.5)
        player.update_effects(0.5)
        self.assertEqual(player.bonus_labels, [])

    def test_reset_clears_effects(self):
        player = game.Player()
        game.on_barrel_jumped(player, game.Barrel())
        player.reset()
        self.assertEqual(player.bonus_labels, [])


class MultiplierTests(unittest.TestCase):
    def test_multiplier_threshold(self):
        for score, expected in [(0, 1), (400, 1), (499, 1), (500, 2), (700, 2), (100000, 2)]:
            with self.subTest(score=score):
                self.assertEqual(game.score_multiplier(score), expected)

    def test_main_loop_awards_each_barrel_once_and_labels_actual_bonus(self):
        player = game.Player()
        player.pos.update(100, 540)
        player.on_ground = False
        created = []
        barrel_type = game.Barrel

        def spawn():
            barrel = barrel_type()
            barrel.pos.update(100, 550)
            created.append(barrel)
            return barrel

        events = [[] for _ in range(26)] + [[game.pygame.event.Event(game.pygame.QUIT)]]
        with patch("game.Player", return_value=player), \
             patch.object(player, "update"), \
             patch.object(barrel_type, "update"), \
             patch("game.Barrel", side_effect=spawn), \
             patch("game.random.uniform", return_value=0), \
             patch("game.pygame.time.Clock", return_value=SimpleNamespace(tick=lambda fps: 50)), \
             patch("game.pygame.event.get", side_effect=events), \
             patch("game.draw_scene", wraps=game.draw_scene) as draw:
            game.main()
        scores = [call.args[4] for call in draw.call_args_list]
        gains = [b - a for a, b in zip([0] + scores, scores) if b != a]
        self.assertGreater(len(gains), 5)
        self.assertEqual(gains[:5], [100] * 5)
        self.assertEqual(gains[5:], [200] * (len(gains) - 5))
        self.assertEqual(len(gains), len(created))
        self.assertTrue(all(barrel.scored for barrel in created))
        self.assertEqual([label.points for label in player.bonus_labels], gains)


if __name__ == "__main__":
    unittest.main()
