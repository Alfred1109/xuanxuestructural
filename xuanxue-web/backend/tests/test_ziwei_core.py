import sys
import unittest

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')

from core.ziwei import ZiWeiChart, analyze_ziwei_chart


class TestZiWeiCore(unittest.TestCase):
    def test_ziwei_chart_builds_core_sections(self):
        chart = ZiWeiChart(1990, 1, 1, 12, 0, "男")
        result = chart.to_dict()

        self.assertIn("minggong", result)
        self.assertIn("shengong", result)
        self.assertIn("major_stars", result)
        self.assertIn("four_transformations", result)
        self.assertIn("core_palaces", result)
        self.assertIn("palaces", result)
        self.assertIn("calc_trace", result)
        self.assertTrue(result["major_stars"])
        self.assertEqual(len(result["palaces"]), 12)

    def test_ziwei_analysis_returns_summary(self):
        chart = ZiWeiChart(1990, 1, 1, 12, 0, "男").to_dict()
        analysis = analyze_ziwei_chart(chart)

        self.assertIn("summary", analysis)
        self.assertIn("career_vector", analysis)
        self.assertIn("wealth_vector", analysis)
        self.assertIn("mutagen_summary", analysis)
        self.assertIn("current_decadal", analysis)
        self.assertIn("advice", analysis)
        self.assertTrue(analysis["summary"])


if __name__ == "__main__":
    unittest.main()
