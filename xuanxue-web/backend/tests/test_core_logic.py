import sys
import unittest

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')

from core.bazi_core import BaZiChart
from core.liuyao import divine
from core.qimen import QiMenChart
from core.zeri import DateSelection
from core.ganzhi import get_month_ganzhi, get_hour_ganzhi
from core.calendar import solar_to_lunar, lunar_to_solar


class TestCoreLogic(unittest.TestCase):
    def test_bazi_month_pillar_uses_solar_terms(self):
        # 立春前（2026-02-03）应属于丑月
        pre_lichun = BaZiChart(2026, 2, 3, 12, 0, '男')
        # 立春后（2026-02-05）应属于寅月
        post_lichun = BaZiChart(2026, 2, 5, 12, 0, '男')

        self.assertTrue(pre_lichun.month_pillar.endswith('丑'))
        self.assertTrue(post_lichun.month_pillar.endswith('寅'))

    def test_shishen_yinyang_mapping(self):
        # 1990-01-01 12:00 男
        # 日干丙(阳火)，年干己(阴土) => 我生且异阴阳，应为伤官
        chart = BaZiChart(1990, 1, 1, 12, 0, '男')
        shishen = chart.get_shishen()
        self.assertEqual(shishen['year_gan'], '伤官')

    def test_dayun_start_age_parameter(self):
        chart = BaZiChart(1990, 1, 1, 12, 0, '男')
        default_dayun = chart.get_dayun()
        custom_dayun = chart.get_dayun(start_age=7)

        self.assertGreaterEqual(default_dayun[0]['start_age'], 1)
        self.assertEqual(custom_dayun[0]['start_age'], 7)
        self.assertEqual(custom_dayun[0]['end_age'], 16)

    def test_dayun_auto_start_age_varies_with_birth_time(self):
        # 同一年内靠近节令边界与远离边界，自动起运年龄应有差异
        near_term = BaZiChart(2026, 2, 4, 23, 0, '男')  # 靠近立春
        far_from_term = BaZiChart(2026, 2, 20, 12, 0, '男')

        age_near = near_term.get_dayun()[0]['start_age']
        age_far = far_from_term.get_dayun()[0]['start_age']

        self.assertNotEqual(age_near, age_far)

    def test_qimen_dun_type_cross_year(self):
        jan_chart = QiMenChart(2026, 1, 15, 10, 0)
        jul_chart = QiMenChart(2026, 7, 15, 10, 0)
        dec_chart = QiMenChart(2026, 12, 25, 10, 0)

        self.assertEqual(jan_chart.dun_type, '阳遁')
        self.assertEqual(jul_chart.dun_type, '阴遁')
        self.assertEqual(dec_chart.dun_type, '阳遁')

    def test_qimen_best_direction_excludes_center(self):
        chart = QiMenChart(2026, 2, 28, 9, 0)
        best = chart.find_best_direction()
        self.assertNotEqual(best['最佳方位'], '中宫')

    def test_qimen_daxiong_scoring_not_shadowed(self):
        chart = QiMenChart(2026, 2, 28, 9, 0)
        chart.chart['坎宫']['门吉凶']['type'] = '大凶'
        chart.chart['坎宫']['星吉凶']['type'] = '中平'
        analysis = chart.analyze_palace('坎宫')

        # 大凶应至少按 -2 计分，不应被“凶”分支提前吞掉
        self.assertLessEqual(analysis['吉凶分数'], -2)

    def test_zeri_shier_shen_changes_by_day(self):
        a = DateSelection(2026, 2, 28).get_shier_shen()
        b = DateSelection(2026, 3, 1).get_shier_shen()
        self.assertNotEqual(a, b)

    def test_liuyao_use_time_is_deterministic_in_same_minute(self):
        r1 = divine('测试', use_time=True)
        r2 = divine('测试', use_time=True)
        self.assertEqual(r1['gua_info']['bengua']['binary'], r2['gua_info']['bengua']['binary'])

    def test_ganzhi_input_validation(self):
        with self.assertRaises(ValueError):
            get_month_ganzhi(2026, 13)
        with self.assertRaises(ValueError):
            get_hour_ganzhi(10, 12)
        with self.assertRaises(ValueError):
            get_hour_ganzhi(1, 24)

    def test_calendar_known_roundtrip(self):
        # 2024-02-10 是农历 2024 年正月初一
        lunar = solar_to_lunar(2024, 2, 10)
        self.assertEqual(lunar[:3], (2024, 1, 1))
        self.assertFalse(lunar[3])

        solar = lunar_to_solar(2024, 1, 1, False)
        self.assertEqual(solar, (2024, 2, 10))


if __name__ == '__main__':
    unittest.main()
