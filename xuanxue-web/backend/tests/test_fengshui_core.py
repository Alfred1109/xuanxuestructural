import sys
import unittest

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')

from core.fengshui import FengShuiReading, normalize_orientation, normalize_scene_type


class TestFengShuiCore(unittest.TestCase):
    def test_orientation_normalization(self):
        self.assertEqual(normalize_orientation("东南向"), "southeast")
        self.assertEqual(normalize_orientation("south"), "south")
        self.assertEqual(normalize_orientation(""), "unknown")

    def test_scene_type_normalization(self):
        self.assertEqual(normalize_scene_type("办公室"), "office")
        self.assertEqual(normalize_scene_type("住宅"), "home")
        self.assertEqual(normalize_scene_type(""), "generic")

    def test_fengshui_reading_returns_scores(self):
        result = FengShuiReading(
            question="这个办公室工位适合我长期坐吗？",
            location="上海浦东办公室",
            orientation="东南向",
            scene_type="office",
            layout_note="背后有靠，前方较开阔，但左侧杂物较多，采光不错。",
        ).to_dict()

        self.assertIn("summary", result)
        self.assertIn("space_support", result)
        self.assertIn("layout_risk", result)
        self.assertIn("calc_trace", result)
        self.assertGreater(result["space_support"], 0)


if __name__ == "__main__":
    unittest.main()
