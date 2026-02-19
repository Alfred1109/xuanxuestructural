"""
天干地支核心算法
Heavenly Stems and Earthly Branches Core Algorithms
"""

# 十天干
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
TIANGAN_EN = ['Jia', 'Yi', 'Bing', 'Ding', 'Wu', 'Ji', 'Geng', 'Xin', 'Ren', 'Gui']

# 十二地支
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
DIZHI_EN = ['Zi', 'Chou', 'Yin', 'Mao', 'Chen', 'Si', 'Wu', 'Wei', 'Shen', 'You', 'Xu', 'Hai']

# 十二生肖
SHENGXIAO = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']

# 五行属性
WUXING_TIANGAN = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水'
}

WUXING_DIZHI = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木',
    '辰': '土', '巳': '火', '午': '火', '未': '土',
    '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

# 阴阳属性
YINYANG_TIANGAN = {
    '甲': '阳', '乙': '阴',
    '丙': '阳', '丁': '阴',
    '戊': '阳', '己': '阴',
    '庚': '阳', '辛': '阴',
    '壬': '阳', '癸': '阴'
}

YINYANG_DIZHI = {
    '子': '阳', '丑': '阴', '寅': '阳', '卯': '阴',
    '辰': '阳', '巳': '阴', '午': '阳', '未': '阴',
    '申': '阳', '酉': '阴', '戌': '阳', '亥': '阴'
}

# 地支藏干
DIZHI_CANGGAN = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '庚', '戊'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲']
}


def get_ganzhi(index: int) -> str:
    """
    根据索引获取干支
    index: 0-59 (六十甲子循环)
    """
    tian = TIANGAN[index % 10]
    di = DIZHI[index % 12]
    return f"{tian}{di}"


def get_year_ganzhi(year: int) -> str:
    """
    计算年份的干支
    以1984年（甲子年）为基准
    """
    # 1984年是甲子年（索引0）
    base_year = 1984
    offset = (year - base_year) % 60
    return get_ganzhi(offset)


def get_month_ganzhi(year: int, month: int) -> str:
    """
    计算月份的干支
    月建：寅月（正月）开始
    """
    # 年干决定月干的起始
    year_gan_index = (year - 1984) % 10
    
    # 月支固定：寅(1月)、卯(2月)、辰(3月)...
    month_zhi_index = (month + 1) % 12  # 寅月为正月
    
    # 月干计算：年干 * 2 + 月份
    # 甲己年丙作首，乙庚年戊为头，丙辛年庚起首，丁壬年壬起头，戊癸年甲为首
    month_gan_base = {
        0: 2, 5: 2,  # 甲、己年从丙开始
        1: 4, 6: 4,  # 乙、庚年从戊开始
        2: 6, 7: 6,  # 丙、辛年从庚开始
        3: 8, 8: 8,  # 丁、壬年从壬开始
        4: 0, 9: 0   # 戊、癸年从甲开始
    }
    
    month_gan_index = (month_gan_base[year_gan_index] + month - 1) % 10
    
    return TIANGAN[month_gan_index] + DIZHI[month_zhi_index]


def get_day_ganzhi(year: int, month: int = None, day: int = None) -> str:
    """
    计算日期的干支
    可以传入：
    1. 单个参数：从基准日期（1900-01-01）开始的天数
    2. 三个参数：年、月、日
    """
    if month is None and day is None:
        # 单参数模式：year实际是days_from_base
        days_from_base = year
    else:
        # 三参数模式：计算从1900-01-01开始的天数
        from datetime import datetime
        base_date = datetime(1900, 1, 1)
        target_date = datetime(year, month, day)
        days_from_base = (target_date - base_date).days
    
    # 1900-01-01 是甲辰日（索引40）
    base_index = 40
    index = (base_index + days_from_base) % 60
    return get_ganzhi(index)


def get_hour_ganzhi(day_gan_index: int, hour: int) -> str:
    """
    计算时辰的干支
    day_gan_index: 日干的索引(0-9)
    hour: 小时(0-23)
    """
    # 时辰对应关系
    hour_to_zhi = {
        (23, 1): 0,   # 子时 23:00-01:00
        (1, 3): 1,    # 丑时 01:00-03:00
        (3, 5): 2,    # 寅时 03:00-05:00
        (5, 7): 3,    # 卯时 05:00-07:00
        (7, 9): 4,    # 辰时 07:00-09:00
        (9, 11): 5,   # 巳时 09:00-11:00
        (11, 13): 6,  # 午时 11:00-13:00
        (13, 15): 7,  # 未时 13:00-15:00
        (15, 17): 8,  # 申时 15:00-17:00
        (17, 19): 9,  # 酉时 17:00-19:00
        (19, 21): 10, # 戌时 19:00-21:00
        (21, 23): 11  # 亥时 21:00-23:00
    }
    
    # 确定时支
    hour_zhi_index = (hour + 1) // 2 % 12
    
    # 时干计算：日干决定时干起始
    # 甲己日甲子时，乙庚日丙子时，丙辛日戊子时，丁壬日庚子时，戊癸日壬子时
    hour_gan_base = {
        0: 0, 5: 0,  # 甲、己日从甲开始
        1: 2, 6: 2,  # 乙、庚日从丙开始
        2: 4, 7: 4,  # 丙、辛日从戊开始
        3: 6, 8: 6,  # 丁、壬日从庚开始
        4: 8, 9: 8   # 戊、癸日从壬开始
    }
    
    hour_gan_index = (hour_gan_base[day_gan_index] + hour_zhi_index) % 10
    
    return TIANGAN[hour_gan_index] + DIZHI[hour_zhi_index]


def get_wuxing(gan_or_zhi: str) -> str:
    """获取天干或地支的五行属性"""
    if gan_or_zhi in WUXING_TIANGAN:
        return WUXING_TIANGAN[gan_or_zhi]
    elif gan_or_zhi in WUXING_DIZHI:
        return WUXING_DIZHI[gan_or_zhi]
    return None


def get_yinyang(gan_or_zhi: str) -> str:
    """获取天干或地支的阴阳属性"""
    if gan_or_zhi in YINYANG_TIANGAN:
        return YINYANG_TIANGAN[gan_or_zhi]
    elif gan_or_zhi in YINYANG_DIZHI:
        return YINYANG_DIZHI[gan_or_zhi]
    return None


def get_nayin(ganzhi: str) -> str:
    """
    获取纳音五行
    六十甲子纳音表
    """
    NAYIN_TABLE = {
        '甲子': '海中金', '乙丑': '海中金',
        '丙寅': '炉中火', '丁卯': '炉中火',
        '戊辰': '大林木', '己巳': '大林木',
        '庚午': '路旁土', '辛未': '路旁土',
        '壬申': '剑锋金', '癸酉': '剑锋金',
        '甲戌': '山头火', '乙亥': '山头火',
        '丙子': '涧下水', '丁丑': '涧下水',
        '戊寅': '城头土', '己卯': '城头土',
        '庚辰': '白蜡金', '辛巳': '白蜡金',
        '壬午': '杨柳木', '癸未': '杨柳木',
        '甲申': '泉中水', '乙酉': '泉中水',
        '丙戌': '屋上土', '丁亥': '屋上土',
        '戊子': '霹雳火', '己丑': '霹雳火',
        '庚寅': '松柏木', '辛卯': '松柏木',
        '壬辰': '长流水', '癸巳': '长流水',
        '甲午': '砂中金', '乙未': '砂中金',
        '丙申': '山下火', '丁酉': '山下火',
        '戊戌': '平地木', '己亥': '平地木',
        '庚子': '壁上土', '辛丑': '壁上土',
        '壬寅': '金箔金', '癸卯': '金箔金',
        '甲辰': '覆灯火', '乙巳': '覆灯火',
        '丙午': '天河水', '丁未': '天河水',
        '戊申': '大驿土', '己酉': '大驿土',
        '庚戌': '钗钏金', '辛亥': '钗钏金',
        '壬子': '桑柘木', '癸丑': '桑柘木',
        '甲寅': '大溪水', '乙卯': '大溪水',
        '丙辰': '沙中土', '丁巳': '沙中土',
        '戊午': '天上火', '己未': '天上火',
        '庚申': '石榴木', '辛酉': '石榴木',
        '壬戌': '大海水', '癸亥': '大海水'
    }
    return NAYIN_TABLE.get(ganzhi, '未知')


if __name__ == "__main__":
    # 测试
    print("=== 天干地支测试 ===")
    print(f"2024年干支: {get_year_ganzhi(2024)}")
    print(f"2024年2月干支: {get_month_ganzhi(2024, 2)}")
    print(f"甲子的纳音: {get_nayin('甲子')}")
