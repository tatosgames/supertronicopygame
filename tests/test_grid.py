import unittest

from config import Config
from renderers.core import LineBatch, Projection
from renderers.landscape import GridRenderer


class GridRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config()
        self.projection = Projection(self.config)
        self.grid = GridRenderer(self.config)

    def test_curve_displaces_near_points_more_than_far_points(self) -> None:
        self.grid.turn_current = 1.0
        floor_y = 1.25
        near = self.grid._project_curved(self.projection, 0.0, floor_y, self.config.grid_z_near)
        far = self.grid._project_curved(self.projection, 0.0, floor_y, self.config.grid_z_far)
        plain_near = self.projection.project(0.0, floor_y, self.config.grid_z_near)
        plain_far = self.projection.project(0.0, floor_y, self.config.grid_z_far)
        self.assertIsNotNone(near)
        self.assertIsNotNone(far)
        self.assertIsNotNone(plain_near)
        self.assertIsNotNone(plain_far)
        self.assertGreater(near[0], plain_near[0])
        self.assertEqual(far[0], plain_far[0])

    def test_curved_grid_uses_multiple_segments_for_depth_lines(self) -> None:
        self.config.grid_curve_segments = 3
        batch = LineBatch()
        self.grid.draw(None, self.projection, 0.0, batch)
        expected_depth_lines = int((self.config.grid_extent_x * 2) / self.config.grid_spacing_x) + 1
        expected_depth_lines += 4
        polyline_segments = sum(len(points) - 1 for points, _, _ in batch.polylines)
        self.assertGreaterEqual(polyline_segments, expected_depth_lines * self.config.grid_curve_segments)

    def test_curve_only_active_during_transition_and_returns_quickly(self) -> None:
        self.grid.turn_current = 0.0
        self.grid.turn_target = 0.8
        self.grid.begin_transition()
        self.grid.turn_target = 0.8
        self.grid.update(1.0, transition_active=True)
        self.assertGreater(self.grid.turn_current, 0.0)
        self.assertLess(self.grid.turn_current, self.grid.turn_target)
        curved_value = self.grid.turn_current
        self.grid.update(0.5, transition_active=False)
        self.assertLess(abs(self.grid.turn_current), abs(curved_value))
        self.grid.update(1.0, transition_active=False)
        self.assertAlmostEqual(self.grid.turn_current, 0.0, delta=0.01)
