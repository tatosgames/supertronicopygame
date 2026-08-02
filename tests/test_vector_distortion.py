import unittest

from config import Config
from renderers.core import VectorDistortion


class VectorDistortionTests(unittest.TestCase):
    def test_no_onset_has_no_offsets(self) -> None:
        distortion = VectorDistortion(Config(height=320))
        self.assertEqual(distortion.offsets(1.0, 0.0), [0] * 16)

    def test_offsets_are_deterministic_and_bounded(self) -> None:
        distortion = VectorDistortion(Config(height=320))
        offsets = distortion.offsets(1.0, 1.0)
        self.assertEqual(offsets, distortion.offsets(1.0, 1.0))
        self.assertTrue(all(-10 <= offset <= 10 for offset in offsets))
        self.assertNotEqual(offsets, distortion.offsets(1.1, 1.0))
