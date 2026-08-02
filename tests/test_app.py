import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from app import App
from cli import parse_args


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = App(parse_args(["--profile", "minimal", "--no-audio", "--no-auto"]))

    def tearDown(self) -> None:
        self.app.close()

    def test_documented_toggle_controls(self) -> None:
        for key, attribute in ((pygame.K_f, "show_fps"), (pygame.K_s, "scanlines"), (pygame.K_g, "glow"), (pygame.K_d, "vector_distortion"), (pygame.K_v, "auto_variation"), (pygame.K_m, "audio_enabled")):
            before = getattr(self.app.config, attribute)
            self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
            self.assertEqual(getattr(self.app.config, attribute), not before)

        previous_palette = self.app.config.palette_index
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
        self.assertEqual(self.app.config.palette_index, (previous_palette + 1) % len(self.app.config.palettes))

    def test_speed_horizon_seed_and_exit_controls(self) -> None:
        speed = self.app.config.speed
        horizon = self.app.config.horizon_ratio
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        self.assertGreater(self.app.config.speed, speed)
        self.assertGreater(self.app.config.horizon_ratio, horizon)

        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.assertIsNotNone(self.app.city.transition_buildings)
        self.assertIsNotNone(self.app.terrain.transition_points)

        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertFalse(self.app.running)

    def test_draws_multiple_headless_frames_and_closes_idempotently(self) -> None:
        for _ in range(3):
            self.app.elapsed += 1.0 / 30.0
            self.app.update(1.0 / 30.0)
            self.app.draw()
        self.assertEqual(self.app.surface.get_size(), (480, 320))
        self.app.close()
        self.app.close()

    def test_draws_audio_vector_distortion_headlessly(self) -> None:
        self.app.config.vector_distortion = True
        self.app.config.audio_onset = 1.0
        self.app.elapsed = 1.0
        self.app.draw()
        self.assertEqual(self.app.surface.get_size(), (480, 320))
