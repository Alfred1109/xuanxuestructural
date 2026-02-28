"""
八字排盘核心算法
BaZi (Eight Characters) Core Engine
"""

from datetime import datetime, timedelta
import math
from typing import Dict, List, Tuple
from .ganzhi import (
    TIANGAN, DIZHI, get_year_ganzhi, get_month_ganzhi,
    get_day_ganzhi, get_hour_ganzhi, get_wuxing, get_yinyang,
    get_nayin, DIZHI_CANGGAN, WUXING_TIANGAN
)
from .calendar import get_lichun_date, solar_to_lunar
from .calendar import get_solar_term_date


class BaZiChart:
    """八字命盘类"""
    
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int = 0, gender: str = '男'):
        self.birth_year = year
        self.birth_month = month
        self.birth_day = day
        self.birth_hour = hour
        self.birth_minute = minute
        self.gender = gender
        
        # 计算八字
        self.year_pillar = None
        self.month_pillar = None
        self.day_pillar = None
        self.hour_pillar = None
        
        self._calculate()
    
    def _calculate(self):
        """计算八字四柱"""
        birth_date = datetime(self.birth_year, self.birth_month, self.birth_day, self.birth_hour, self.birth_minute)
        
        # 1. 年柱：以立春为界
        lichun = get_lichun_date(self.birth_year)
        if birth_date < lichun:
            # 立春前算上一年
            year_for_ganzhi = self.birth_year - 1
        else:
            year_for_ganzhi = self.birth_year
        
        self.year_pillar = get_year_ganzhi(year_for_ganzhi)
        
        # 2. 月柱：按节令月（寅月起于立春）计算
        month_index = self._get_bazi_month_index(birth_date)
        self.month_pillar = get_month_ganzhi(year_for_ganzhi, month_index)
        
        # 3. 日柱：计算从1900-01-01开始的天数
        base_date = datetime(1900, 1, 1)
        days_diff = (birth_date - base_date).days
        self.day_pillar = get_day_ganzhi(days_diff)
        
        # 4. 时柱
        day_gan_index = TIANGAN.index(self.day_pillar[0])
        self.hour_pillar = get_hour_ganzhi(day_gan_index, self.birth_hour)

    def _get_bazi_month_index(self, birth_date: datetime) -> int:
        """
        根据节气边界计算八字月序：
        寅月=1, 卯月=2, ... 子月=11, 丑月=12
        """
        year = birth_date.year
        lichun_cur = get_solar_term_date(year, 2)

        # 立春后使用当年节令序列，立春前使用上一年节令序列
        if birth_date >= lichun_cur:
            base_year = year
            next_year = year + 1
        else:
            base_year = year - 1
            next_year = year

        boundaries = [
            (get_solar_term_date(base_year, 2), 1),   # 立春 -> 寅月
            (get_solar_term_date(base_year, 4), 2),   # 惊蛰 -> 卯月
            (get_solar_term_date(base_year, 6), 3),   # 清明 -> 辰月
            (get_solar_term_date(base_year, 8), 4),   # 立夏 -> 巳月
            (get_solar_term_date(base_year, 10), 5),  # 芒种 -> 午月
            (get_solar_term_date(base_year, 12), 6),  # 小暑 -> 未月
            (get_solar_term_date(base_year, 14), 7),  # 立秋 -> 申月
            (get_solar_term_date(base_year, 16), 8),  # 白露 -> 酉月
            (get_solar_term_date(base_year, 18), 9),  # 寒露 -> 戌月
            (get_solar_term_date(base_year, 20), 10), # 立冬 -> 亥月
            (get_solar_term_date(base_year, 22), 11), # 大雪 -> 子月
            (get_solar_term_date(next_year, 0), 12),  # 小寒 -> 丑月
        ]

        month_index = 12  # 默认丑月（兜底）
        for boundary, idx in boundaries:
            if birth_date >= boundary:
                month_index = idx
            else:
                break

        return month_index
    
    def get_pillars(self) -> Dict[str, str]:
        """获取四柱"""
        return {
            'year': self.year_pillar,
            'month': self.month_pillar,
            'day': self.day_pillar,
            'hour': self.hour_pillar
        }
    
    def get_tiangan(self) -> List[str]:
        """获取四天干"""
        return [
            self.year_pillar[0],
            self.month_pillar[0],
            self.day_pillar[0],
            self.hour_pillar[0]
        ]
    
    def get_dizhi(self) -> List[str]:
        """获取四地支"""
        return [
            self.year_pillar[1],
            self.month_pillar[1],
            self.day_pillar[1],
            self.hour_pillar[1]
        ]
    
    def get_wuxing_count(self) -> Dict[str, int]:
        """统计五行数量"""
        count = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
        
        # 统计天干
        for gan in self.get_tiangan():
            wuxing = get_wuxing(gan)
            count[wuxing] += 1
        
        # 统计地支
        for zhi in self.get_dizhi():
            wuxing = get_wuxing(zhi)
            count[wuxing] += 1
        
        # 统计地支藏干
        for zhi in self.get_dizhi():
            for canggan in DIZHI_CANGGAN[zhi]:
                wuxing = get_wuxing(canggan)
                count[wuxing] += 0.5  # 藏干权重减半
        
        return count
    
    def get_shishen(self) -> Dict[str, List[str]]:
        """
        计算十神
        以日干为我，其他干支与日干的关系
        """
        day_gan = self.day_pillar[0]
        day_wuxing = get_wuxing(day_gan)
        day_yinyang = get_yinyang(day_gan)
        
        # 十神关系表
        shishen_map = {
            ('同', '同'): '比肩',
            ('同', '异'): '劫财',
            # 阴阳同者为偏，异者为正（比劫除外）
            ('生我', '同'): '偏印',
            ('生我', '异'): '正印',
            ('我生', '同'): '食神',
            ('我生', '异'): '伤官',
            ('我克', '同'): '偏财',
            ('我克', '异'): '正财',
            ('克我', '同'): '七杀',
            ('克我', '异'): '正官'
        }
        
        # 五行生克关系
        wuxing_relation = {
            '木': {'生': '火', '克': '土', '生我': '水', '克我': '金'},
            '火': {'生': '土', '克': '金', '生我': '木', '克我': '水'},
            '土': {'生': '金', '克': '水', '生我': '火', '克我': '木'},
            '金': {'生': '水', '克': '木', '生我': '土', '克我': '火'},
            '水': {'生': '木', '克': '火', '生我': '金', '克我': '土'}
        }
        
        result = {
            'year_gan': None,
            'month_gan': None,
            'day_gan': '日主',
            'hour_gan': None
        }
        
        pillars = ['year', 'month', 'day', 'hour']
        for i, pillar in enumerate(pillars):
            if pillar == 'day':
                continue
            
            gan = self.get_tiangan()[i]
            gan_wuxing = get_wuxing(gan)
            gan_yinyang = get_yinyang(gan)
            
            # 判断关系
            if gan_wuxing == day_wuxing:
                relation = '同'
            elif wuxing_relation[day_wuxing]['生'] == gan_wuxing:
                relation = '我生'
            elif wuxing_relation[day_wuxing]['克'] == gan_wuxing:
                relation = '我克'
            elif wuxing_relation[day_wuxing]['生我'] == gan_wuxing:
                relation = '生我'
            elif wuxing_relation[day_wuxing]['克我'] == gan_wuxing:
                relation = '克我'
            else:
                relation = '未知'
            
            # 判断阴阳
            yinyang = '同' if gan_yinyang == day_yinyang else '异'
            
            # 查找十神
            shishen = shishen_map.get((relation, yinyang), '未知')
            result[f'{pillar}_gan'] = shishen
        
        return result
    
    def get_dayun(self, start_age: int = None) -> List[Dict]:
        """
        计算大运
        男命阳年生、女命阴年生：顺排
        男命阴年生、女命阳年生：逆排
        """
        year_gan = self.year_pillar[0]
        year_yinyang = get_yinyang(year_gan)
        
        # 判断顺逆
        if (self.gender == '男' and year_yinyang == '阳') or (self.gender == '女' and year_yinyang == '阴'):
            direction = 1  # 顺排
        else:
            direction = -1  # 逆排
        
        # 从月柱开始排大运
        month_gan_index = TIANGAN.index(self.month_pillar[0])
        month_zhi_index = DIZHI.index(self.month_pillar[1])
        
        dayun_list = []
        # 起运年龄：支持外部指定；未指定时按“出生与节令差值/3”自动估算
        if start_age is not None:
            base_start_age = start_age
        else:
            base_start_age = self._estimate_dayun_start_age(direction)

        for i in range(8):  # 排8步大运
            gan_index = (month_gan_index + direction * (i + 1)) % 10
            zhi_index = (month_zhi_index + direction * (i + 1)) % 12
            
            dayun_ganzhi = TIANGAN[gan_index] + DIZHI[zhi_index]
            current_start_age = base_start_age + i * 10  # 简化处理，实际应该根据出生日期到节气的天数计算
            
            dayun_list.append({
                'ganzhi': dayun_ganzhi,
                'start_age': current_start_age,
                'end_age': current_start_age + 9
            })
        
        return dayun_list

    def _estimate_dayun_start_age(self, direction: int) -> int:
        """
        估算起运年龄（简化）：
        - 顺排：取出生后到下一“节”的天数
        - 逆排：取出生前到上一“节”的天数
        按传统换算约“3天=1岁”
        """
        birth_dt = datetime(
            self.birth_year, self.birth_month, self.birth_day, self.birth_hour, self.birth_minute
        )
        prev_jie, next_jie = self._get_prev_next_jieqi(birth_dt)

        if direction == 1:
            delta_days = (next_jie - birth_dt).total_seconds() / 86400
        else:
            delta_days = (birth_dt - prev_jie).total_seconds() / 86400

        # 最少按1岁起运；向上取整避免低估
        return max(1, int(math.ceil(delta_days / 3.0)))

    def _get_prev_next_jieqi(self, dt: datetime) -> Tuple[datetime, datetime]:
        """获取某时刻前后最近的“节”（12节，不含中气）"""
        # 12节索引：小寒、立春、惊蛰、清明、立夏、芒种、小暑、立秋、白露、寒露、立冬、大雪
        jie_indexes = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]

        candidates = []
        for y in (dt.year - 1, dt.year, dt.year + 1):
            for idx in jie_indexes:
                candidates.append(get_solar_term_date(y, idx))
        candidates.sort()

        prev_jie = candidates[0]
        next_jie = candidates[-1]
        for term_dt in candidates:
            if term_dt <= dt:
                prev_jie = term_dt
            if term_dt > dt:
                next_jie = term_dt
                break

        return prev_jie, next_jie
    
    def get_nayin_all(self) -> Dict[str, str]:
        """获取四柱纳音"""
        return {
            'year': get_nayin(self.year_pillar),
            'month': get_nayin(self.month_pillar),
            'day': get_nayin(self.day_pillar),
            'hour': get_nayin(self.hour_pillar)
        }
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        lunar = solar_to_lunar(self.birth_year, self.birth_month, self.birth_day)
        
        return {
            'birth_info': {
                'solar': {
                    'year': self.birth_year,
                    'month': self.birth_month,
                    'day': self.birth_day,
                    'hour': self.birth_hour,
                    'minute': self.birth_minute
                },
                'lunar': {
                    'year': lunar[0],
                    'month': lunar[1],
                    'day': lunar[2],
                    'is_leap': lunar[3]
                },
                'gender': self.gender
            },
            'bazi': {
                'year': self.year_pillar,
                'month': self.month_pillar,
                'day': self.day_pillar,
                'hour': self.hour_pillar
            },
            'tiangan': self.get_tiangan(),
            'dizhi': self.get_dizhi(),
            'wuxing_count': self.get_wuxing_count(),
            'shishen': self.get_shishen(),
            'nayin': self.get_nayin_all(),
            'dayun': self.get_dayun()
        }


if __name__ == "__main__":
    # 测试
    print("=== 八字排盘测试 ===")
    
    # 示例：1990年1月1日12时出生的男性
    chart = BaZiChart(1990, 1, 1, 12, 0, '男')
    
    print(f"\n出生信息：1990年1月1日12时")
    print(f"年柱：{chart.year_pillar}")
    print(f"月柱：{chart.month_pillar}")
    print(f"日柱：{chart.day_pillar}")
    print(f"时柱：{chart.hour_pillar}")
    
    print(f"\n五行统计：{chart.get_wuxing_count()}")
    print(f"\n十神：{chart.get_shishen()}")
    
    print(f"\n大运：")
    for dayun in chart.get_dayun():
        print(f"  {dayun['start_age']}-{dayun['end_age']}岁: {dayun['ganzhi']}")
