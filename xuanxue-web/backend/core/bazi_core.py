"""
八字排盘核心算法
BaZi (Eight Characters) Core Engine
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from .ganzhi import (
    TIANGAN, DIZHI, get_year_ganzhi, get_month_ganzhi,
    get_day_ganzhi, get_hour_ganzhi, get_wuxing, get_yinyang,
    get_nayin, DIZHI_CANGGAN, WUXING_TIANGAN
)
from .calendar import get_lichun_date, solar_to_lunar


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
        
        # 2. 月柱：以节气为界（简化处理，实际应该精确到节气时刻）
        self.month_pillar = get_month_ganzhi(year_for_ganzhi, self.birth_month)
        
        # 3. 日柱：计算从1900-01-01开始的天数
        base_date = datetime(1900, 1, 1)
        days_diff = (birth_date - base_date).days
        self.day_pillar = get_day_ganzhi(days_diff)
        
        # 4. 时柱
        day_gan_index = TIANGAN.index(self.day_pillar[0])
        self.hour_pillar = get_hour_ganzhi(day_gan_index, self.birth_hour)
    
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
            ('生我', '同'): '正印',
            ('生我', '异'): '偏印',
            ('我生', '同'): '伤官',
            ('我生', '异'): '食神',
            ('我克', '同'): '正财',
            ('我克', '异'): '偏财',
            ('克我', '同'): '正官',
            ('克我', '异'): '七杀'
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
        for i in range(8):  # 排8步大运
            gan_index = (month_gan_index + direction * (i + 1)) % 10
            zhi_index = (month_zhi_index + direction * (i + 1)) % 12
            
            dayun_ganzhi = TIANGAN[gan_index] + DIZHI[zhi_index]
            start_age = 1 + i * 10  # 简化处理，实际应该根据出生日期到节气的天数计算
            
            dayun_list.append({
                'ganzhi': dayun_ganzhi,
                'start_age': start_age,
                'end_age': start_age + 9
            })
        
        return dayun_list
    
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
