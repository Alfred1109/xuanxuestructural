"""
择日学模块 - 黄道吉日选择
Date Selection Module - Auspicious Days
"""

from datetime import datetime, timedelta
from typing import Dict, List
from .ganzhi import get_year_ganzhi, get_month_ganzhi, get_day_ganzhi, get_wuxing, DIZHI


# 二十八星宿
ERSHIBA_XINGXIU = [
    '角', '亢', '氐', '房', '心', '尾', '箕',  # 东方青龙
    '斗', '牛', '女', '虚', '危', '室', '壁',  # 北方玄武
    '奎', '娄', '胃', '昴', '毕', '觜', '参',  # 西方白虎
    '井', '鬼', '柳', '星', '张', '翼', '轸'   # 南方朱雀
]

# 十二建星
JIANXING = ['建', '除', '满', '平', '定', '执', '破', '危', '成', '收', '开', '闭']

# 建星吉凶
JIANXING_JIXIONG = {
    '建': {'level': '中', 'suitable': ['祭祀', '祈福', '求嗣', '上册'], 'avoid': ['动土', '开仓', '出行']},
    '除': {'level': '吉', 'suitable': ['除旧', '沐浴', '求医', '破屋'], 'avoid': ['结婚', '赴任']},
    '满': {'level': '吉', 'suitable': ['祈福', '结婚', '开市', '交易'], 'avoid': ['栽种', '下葬', '求医']},
    '平': {'level': '吉', 'suitable': ['修造', '动土', '栽种', '纳畜'], 'avoid': ['破土', '安葬']},
    '定': {'level': '吉', 'suitable': ['结婚', '开市', '立券', '交易'], 'avoid': ['诉讼', '出行']},
    '执': {'level': '凶', 'suitable': ['祭祀', '祈福', '捕捉'], 'avoid': ['结婚', '搬家', '出行']},
    '破': {'level': '大凶', 'suitable': ['破屋', '坏垣', '求医'], 'avoid': ['诸事不宜']},
    '危': {'level': '凶', 'suitable': ['安床', '祭祀'], 'avoid': ['登高', '出行', '结婚']},
    '成': {'level': '吉', 'suitable': ['开业', '结婚', '入学', '赴任'], 'avoid': ['诉讼', '拆卸']},
    '收': {'level': '吉', 'suitable': ['收藏', '纳财', '收割'], 'avoid': ['开市', '求医']},
    '开': {'level': '吉', 'suitable': ['开业', '结婚', '出行', '搬家'], 'avoid': ['安葬', '破土']},
    '闭': {'level': '凶', 'suitable': ['修造', '筑堤', '补垣'], 'avoid': ['开市', '出行', '求财']}
}

# 黄道黑道
HUANGDAO_HEIDAO = {
    '青龙': '黄道', '明堂': '黄道', '金匮': '黄道', '天德': '黄道', '玉堂': '黄道', '司命': '黄道',
    '天刑': '黑道', '朱雀': '黑道', '白虎': '黑道', '天牢': '黑道', '玄武': '黑道', '勾陈': '黑道'
}

# 十二神
SHIER_SHEN = ['青龙', '明堂', '天刑', '朱雀', '金匮', '天德', '白虎', '玉堂', '天牢', '玄武', '司命', '勾陈']

# 彭祖百忌
PENGZU_BAIJI = {
    '甲': '不开仓财物耗散', '乙': '不栽植千株不长', '丙': '不修灶必见灾殃', '丁': '不剃头头必生疮',
    '戊': '不受田田主不祥', '己': '不破券二比并亡', '庚': '不经络织机虚张', '辛': '不合酱主人不尝',
    '壬': '不汲水更难提防', '癸': '不词讼理弱敌强',
    '子': '不问卜自惹祸殃', '丑': '不冠带主不还乡', '寅': '不祭祀神鬼不尝', '卯': '不穿井水泉不香',
    '辰': '不哭泣必主重丧', '巳': '不远行财物伏藏', '午': '不苫盖屋主更张', '未': '不服药毒气入肠',
    '申': '不安床鬼祟入房', '酉': '不会客醉坐颠狂', '戌': '不吃犬作怪上床', '亥': '不嫁娶不利新郎'
}


class DateSelection:
    """择日类"""
    
    def __init__(self, year: int, month: int, day: int):
        self.year = year
        self.month = month
        self.day = day
        self.date = datetime(year, month, day)
        
    def get_jianxing(self) -> str:
        """获取建星"""
        # 简化算法：根据月支和日支计算
        month_ganzhi = get_month_ganzhi(self.year, self.month)
        day_ganzhi = get_day_ganzhi(self.year, self.month, self.day)
        
        month_zhi = month_ganzhi[1]
        day_zhi = day_ganzhi[1]
        
        month_index = DIZHI.index(month_zhi)
        day_index = DIZHI.index(day_zhi)
        
        # 建星从月建开始顺数
        jianxing_index = (day_index - month_index) % 12
        return JIANXING[jianxing_index]
    
    def get_shier_shen(self) -> str:
        """获取十二神（黄道黑道）"""
        day_ganzhi = get_day_ganzhi(self.year, self.month, self.day)
        day_gan = day_ganzhi[0]
        
        # 根据日干确定起始神
        start_map = {
            '甲': 0, '己': 0,  # 甲己日从青龙起
            '乙': 5, '庚': 5,  # 乙庚日从天德起
            '丙': 10, '辛': 10,  # 丙辛日从司命起
            '丁': 3, '壬': 3,  # 丁壬日从朱雀起
            '戊': 7, '癸': 7   # 戊癸日从玉堂起
        }
        
        start_index = start_map.get(day_gan, 0)
        hour_index = self.date.hour // 2  # 时辰索引
        shen_index = (start_index + hour_index) % 12
        
        return SHIER_SHEN[shen_index]
    
    def get_xingxiu(self) -> str:
        """获取星宿"""
        # 简化算法：根据日期循环
        days_from_epoch = (self.date - datetime(2000, 1, 1)).days
        xingxiu_index = days_from_epoch % 28
        return ERSHIBA_XINGXIU[xingxiu_index]
    
    def get_pengzu_baiji(self) -> Dict[str, str]:
        """获取彭祖百忌"""
        day_ganzhi = get_day_ganzhi(self.year, self.month, self.day)
        day_gan = day_ganzhi[0]
        day_zhi = day_ganzhi[1]
        
        return {
            'gan_ji': PENGZU_BAIJI.get(day_gan, ''),
            'zhi_ji': PENGZU_BAIJI.get(day_zhi, '')
        }
    
    def analyze_day(self) -> Dict:
        """分析日期吉凶"""
        jianxing = self.get_jianxing()
        shier_shen = self.get_shier_shen()
        xingxiu = self.get_xingxiu()
        pengzu = self.get_pengzu_baiji()
        
        jianxing_info = JIANXING_JIXIONG.get(jianxing, {})
        huangdao_type = HUANGDAO_HEIDAO.get(shier_shen, '未知')
        
        # 综合评分
        score = 50  # 基础分
        
        if jianxing_info.get('level') == '吉':
            score += 15
        elif jianxing_info.get('level') == '大吉':
            score += 25
        elif jianxing_info.get('level') == '凶':
            score -= 15
        elif jianxing_info.get('level') == '大凶':
            score -= 30
        
        if huangdao_type == '黄道':
            score += 20
        elif huangdao_type == '黑道':
            score -= 20
        
        # 判断等级
        if score >= 80:
            level = '大吉'
            color = '#4caf50'
        elif score >= 65:
            level = '吉'
            color = '#8bc34a'
        elif score >= 50:
            level = '平'
            color = '#ff9800'
        elif score >= 35:
            level = '凶'
            color = '#f44336'
        else:
            level = '大凶'
            color = '#d32f2f'
        
        return {
            'date': f'{self.year}年{self.month}月{self.day}日',
            'ganzhi': get_day_ganzhi(self.year, self.month, self.day),
            'jianxing': jianxing,
            'jianxing_info': jianxing_info,
            'shier_shen': shier_shen,
            'huangdao_type': huangdao_type,
            'xingxiu': xingxiu,
            'pengzu_baiji': pengzu,
            'score': score,
            'level': level,
            'color': color,
            'suitable': jianxing_info.get('suitable', []),
            'avoid': jianxing_info.get('avoid', [])
        }


def find_auspicious_days(year: int, month: int, purpose: str = '通用', days: int = 30) -> List[Dict]:
    """
    查找吉日
    
    Args:
        year: 年份
        month: 月份
        purpose: 用途（结婚、开业、搬家、出行等）
        days: 查找天数
    
    Returns:
        吉日列表
    """
    start_date = datetime(year, month, 1)
    results = []
    
    # 用途关键词映射
    purpose_keywords = {
        '结婚': ['结婚', '嫁娶', '婚姻'],
        '开业': ['开业', '开市', '开张', '交易'],
        '搬家': ['搬家', '移徙', '入宅'],
        '出行': ['出行', '远行', '旅游'],
        '动土': ['动土', '修造', '装修'],
        '安葬': ['安葬', '下葬', '葬礼'],
        '祈福': ['祈福', '祭祀', '求神'],
        '求财': ['求财', '纳财', '开市']
    }
    
    keywords = purpose_keywords.get(purpose, [])
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        selector = DateSelection(current_date.year, current_date.month, current_date.day)
        analysis = selector.analyze_day()
        
        # 如果指定了用途，检查是否适合
        if purpose != '通用' and keywords:
            is_suitable = any(kw in ' '.join(analysis['suitable']) for kw in keywords)
            is_avoid = any(kw in ' '.join(analysis['avoid']) for kw in keywords)
            
            if is_avoid:
                continue
            if not is_suitable and analysis['score'] < 60:
                continue
        
        # 只返回平以上的日子
        if analysis['score'] >= 50:
            analysis['weekday'] = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][current_date.weekday()]
            results.append(analysis)
    
    # 按分数排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results


def get_today_fortune(year: int, month: int, day: int) -> Dict:
    """获取今日运势"""
    selector = DateSelection(year, month, day)
    analysis = selector.analyze_day()
    
    # 添加详细建议
    level = analysis['level']
    
    fortune_advice = {
        '大吉': '今日诸事皆宜，是难得的黄道吉日。适合开展重要事务，把握机会，积极进取。',
        '吉': '今日运势良好，大部分事情都可以顺利进行。保持积极心态，稳步前进。',
        '平': '今日运势平稳，宜守不宜攻。处理日常事务即可，不宜开展重大事项。',
        '凶': '今日运势欠佳，诸事需谨慎。避免重要决策，多加小心为上。',
        '大凶': '今日运势不利，宜静不宜动。避免重要事务，以守为主，等待时机。'
    }
    
    analysis['fortune_advice'] = fortune_advice.get(level, '')
    analysis['weekday'] = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][
        datetime(year, month, day).weekday()
    ]
    
    return analysis


if __name__ == "__main__":
    # 测试
    print("=== 择日学测试 ===\n")
    
    # 测试今日运势
    today = datetime.now()
    fortune = get_today_fortune(today.year, today.month, today.day)
    print(f"今日：{fortune['date']} {fortune['weekday']}")
    print(f"干支：{fortune['ganzhi']}")
    print(f"建星：{fortune['jianxing']}")
    print(f"十二神：{fortune['shier_shen']} ({fortune['huangdao_type']})")
    print(f"星宿：{fortune['xingxiu']}")
    print(f"吉凶：{fortune['level']} (评分：{fortune['score']})")
    print(f"宜：{', '.join(fortune['suitable'])}")
    print(f"忌：{', '.join(fortune['avoid'])}")
    print(f"\n建议：{fortune['fortune_advice']}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试查找吉日
    print("查找本月适合结婚的吉日：\n")
    auspicious_days = find_auspicious_days(today.year, today.month, '结婚', 30)
    
    for i, day in enumerate(auspicious_days[:5], 1):
        print(f"{i}. {day['date']} {day['weekday']} - {day['level']} (评分：{day['score']})")
        print(f"   {day['ganzhi']} {day['jianxing']} {day['shier_shen']}")
        print(f"   宜：{', '.join(day['suitable'][:3])}")
        print()
