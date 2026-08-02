import unittest

from cli import parse_args


class CliTests(unittest.TestCase):
    def test_clamps_display_arguments_and_disables_optional_features(self) -> None:
        config = parse_args(["--width", "1", "--height", "1", "--scale", "0", "--fps", "999", "--no-auto", "--no-audio"])
        self.assertEqual((config.width, config.height, config.scale, config.fps), (160, 120, 1, 120))
        self.assertFalse(config.auto_variation)
        self.assertFalse(config.audio_enabled)

    def test_pi_profile_keeps_the_documented_budget(self) -> None:
        config = parse_args(["--profile", "pi"])
        self.assertFalse(config.glow)
        self.assertFalse(config.vector_distortion)
        self.assertFalse(config.flicker)
        self.assertEqual((config.mountain_count, config.city_count, config.drone_count), (34, 18, 4))
        self.assertEqual((config.star_count, config.data_column_count, config.grid_z_far), (46, 10, 32.0))

    def test_minimal_profile_disables_the_expensive_effects(self) -> None:
        config = parse_args(["--profile", "minimal"])
        self.assertFalse(config.glow)
        self.assertFalse(config.scanlines)
        self.assertFalse(config.vector_distortion)
        self.assertFalse(config.flicker)
        self.assertEqual((config.mountain_count, config.city_count, config.drone_count), (26, 14, 2))
        self.assertEqual((config.star_count, config.data_column_count, config.grid_z_far), (22, 5, 26.0))
