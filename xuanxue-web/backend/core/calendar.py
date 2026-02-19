"""
万年历算法 - 阴阳历转换
Lunar-Solar Calendar Conversion
"""

from datetime import datetime, timedelta
from typing import Tuple

# 农历数据：1900-2100年
# 每个数字的后12位表示12个月（1=大月30天，0=小月29天）
# 前4位表示闰月月份（0表示无闰月）
LUNAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,
    0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,
    0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,
    0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,
    0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5d0, 0x14573, 0x052d0, 0x0a9a8, 0x0e950, 0x06aa0,
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,
    0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b5a0, 0x195a6,
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,
    0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,
    0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,
    0x05aa0, 0x076a3, 0x096d0, 0x04bd7, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,
    0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,
    0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0,
    0x0a2e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,
    0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,
    0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,
    0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,
    0x0d520
]

# 节气数据（简化版，实际应该更精确）
SOLAR_TERMS = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分",
    "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
    "小暑", "大暑", "立秋", "处暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"
]


def lunar_year_days(year: int) -> int:
    """计算农历年的总天数"""
    if year < 1900 or year > 2100:
        return 0
    
    sum_days = 348  # 12个月，每月29天
    info = LUNAR_INFO[year - 1900]
    
    # 计算12个月的大小月
    for i in range(12):
        if info & (0x10000 >> i):
            sum_days += 1
    
    # 加上闰月天数
    if leap_month(year):
        if info & 0x10000:
            sum_days += 30
        else:
            sum_days += 29
    
    return sum_days


def leap_month(year: int) -> int:
    """返回农历年的闰月月份，无闰月返回0"""
    if year < 1900 or year > 2100:
        return 0
    return LUNAR_INFO[year - 1900] & 0xf


def leap_days(year: int) -> int:
    """返回农历年闰月的天数"""
    if leap_month(year):
        if LUNAR_INFO[year - 1900] & 0x10000:
            return 30
        else:
            return 29
    return 0


def lunar_month_days(year: int, month: int) -> int:
    """返回农历年月的天数"""
    if year < 1900 or year > 2100:
        return 0
    if LUNAR_INFO[year - 1900] & (0x10000 >> month):
        return 30
    else:
        return 29


def solar_to_lunar(year: int, month: int, day: int) -> Tuple[int, int, int, bool]:
    """
    阳历转农历
    返回: (农历年, 农历月, 农历日, 是否闰月)
    """
    # 基准日期：1900年1月31日，农历1900年正月初一
    base_date = datetime(1900, 1, 31)
    target_date = datetime(year, month, day)
    
    offset = (target_date - base_date).days
    
    # 计算农历年份
    lunar_year = 1900
    temp = 0
    while lunar_year < 2101 and offset > 0:
        temp = lunar_year_days(lunar_year)
        offset -= temp
        lunar_year += 1
    
    if offset < 0:
        offset += temp
        lunar_year -= 1
    
    # 计算农历月份
    leap = leap_month(lunar_year)
    is_leap = False
    lunar_month = 1
    
    while lunar_month < 13 and offset > 0:
        # 闰月
        if leap > 0 and lunar_month == (leap + 1) and not is_leap:
            lunar_month -= 1
            is_leap = True
            temp = leap_days(lunar_year)
        else:
            temp = lunar_month_days(lunar_year, lunar_month)
        
        # 解除闰月
        if is_leap and lunar_month == (leap + 1):
            is_leap = False
        
        offset -= temp
        lunar_month += 1
    
    if offset < 0:
        offset += temp
        lunar_month -= 1
    
    lunar_day = offset + 1
    
    return (lunar_year, lunar_month, lunar_day, is_leap)


def lunar_to_solar(year: int, month: int, day: int, is_leap: bool = False) -> Tuple[int, int, int]:
    """
    农历转阳历
    返回: (阳历年, 阳历月, 阳历日)
    """
    # 基准日期：1900年1月31日，农历1900年正月初一
    base_date = datetime(1900, 1, 31)
    
    offset = 0
    
    # 累加年份天数
    for y in range(1900, year):
        offset += lunar_year_days(y)
    
    # 累加月份天数
    leap = leap_month(year)
    for m in range(1, month):
        offset += lunar_month_days(year, m)
        # 如果是闰月之后的月份，加上闰月天数
        if leap > 0 and m == leap:
            offset += leap_days(year)
    
    # 如果当前是闰月
    if is_leap and leap == month:
        offset += lunar_month_days(year, month)
    
    # 加上日期
    offset += day - 1
    
    result_date = base_date + timedelta(days=offset)
    return (result_date.year, result_date.month, result_date.day)


def get_solar_term_date(year: int, term_index: int) -> datetime:
    """
    获取节气日期（简化算法）
    term_index: 0-23 (小寒到冬至)
    """
    # 这是一个简化的算法，实际应该使用更精确的天文算法
    # 节气大约每15天一个
    base_dates = [
        (1, 5), (1, 20), (2, 4), (2, 19), (3, 5), (3, 20),
        (4, 4), (4, 20), (5, 5), (5, 21), (6, 5), (6, 21),
        (7, 7), (7, 22), (8, 7), (8, 23), (9, 7), (9, 23),
        (10, 8), (10, 23), (11, 7), (11, 22), (12, 7), (12, 21)
    ]
    
    month, day = base_dates[term_index]
    return datetime(year, month, day)


def get_lichun_date(year: int) -> datetime:
    """获取立春日期（八字年份的分界点）"""
    return get_solar_term_date(year, 2)  # 立春是第3个节气（索引2）


if __name__ == "__main__":
    # 测试
    print("=== 万年历测试 ===")
    
    # 阳历转农历
    lunar = solar_to_lunar(2024, 2, 10)
    print(f"2024年2月10日 -> 农历{lunar[0]}年{lunar[1]}月{lunar[2]}日")
    
    # 农历转阳历
    solar = lunar_to_solar(2024, 1, 1)
    print(f"农历2024年正月初一 -> 阳历{solar[0]}年{solar[1]}月{solar[2]}日")
    
    # 立春日期
    lichun = get_lichun_date(2024)
    print(f"2024年立春: {lichun.strftime('%Y年%m月%d日')}")
