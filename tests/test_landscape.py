import unittest

from config import Config
from renderers.landscape import CityRenderer


class CityGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config(city_count=24)

    def test_generation_is_deterministic_for_a_seed(self) -> None:
        first = CityRenderer(self.config)._make_buildings(1234)
        second = CityRenderer(self.config)._make_buildings(1234)
        self.assertEqual(first, second)

    def test_different_seeds_change_the_skyline(self) -> None:
        first = CityRenderer(self.config)._make_buildings(1234)
        second = CityRenderer(self.config)._make_buildings(5678)
        self.assertNotEqual(first, second)

    def test_buildings_stay_within_bounds_and_do_not_overlap(self) -> None:
        buildings = CityRenderer(self.config)._make_buildings(1234)
        self.assertLessEqual(len(buildings), self.config.city_count)
        for building in buildings:
            self.assertGreaterEqual(building.w, self.config.city_min_width)
            self.assertLessEqual(building.w, self.config.city_max_width)
            self.assertGreaterEqual(building.h, self.config.city_min_height)
            self.assertLessEqual(building.h, self.config.city_max_height)
            self.assertGreaterEqual(building.x, self.config.city_span_left)
            self.assertLessEqual(building.x + building.w, self.config.city_span_right)
        for left, right in zip(buildings, buildings[1:]):
            self.assertLessEqual(left.x + left.w, right.x)

    def test_seed_can_produce_multiple_architectural_profiles(self) -> None:
        buildings = CityRenderer(self.config)._make_buildings(1234)
        self.assertGreaterEqual(len({building.profile for building in buildings}), 3)


if __name__ == "__main__":
    unittest.main()
