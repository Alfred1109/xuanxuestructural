"""
奇门遁甲核心模块
Qi Men Dun Jia (Mysterious Door Escaping Technique)
"""

from datetime import datetime
from typing import Dict, List, Tuple
from .ganzhi import get_year_ganzhi, get_month_ganzhi, get_day_ganzhi, get_hour_ganzhi
from .calendar import get_solar_term_date


class QiMenChart:
    """奇门遁甲排盘"""
    
    # 九宫位置（洛书九宫）
    PALACES = {
        4: "巽宫", 9: "离宫", 2: "坤宫",
        3: "震宫", 5: "中宫", 7: "兑宫",
        8: "艮宫", 1: "坎宫", 6: "乾宫"
    }
    
    # 八门
    EIGHT_GATES = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
    
    # 九星
    NINE_STARS = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]
    
    # 八神
    EIGHT_SPIRITS = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
    
    # 三奇六仪
    TIANGAN_ORDER = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    
    # 门吉凶
    GATE_FORTUNE = {
        "开门": {"type": "大吉", "desc": "万事开头，百事可为"},
        "休门": {"type": "吉", "desc": "休养生息，宜静不宜动"},
        "生门": {"type": "大吉", "desc": "生机勃勃，求财求生"},
        "伤门": {"type": "凶", "desc": "伤害损失，宜防不宜攻"},
        "杜门": {"type": "凶", "desc": "闭塞不通，宜守不宜进"},
        "景门": {"type": "中平", "desc": "虚火虚名，外强中干"},
        "死门": {"type": "大凶", "desc": "死气沉沉，万事不利"},
        "惊门": {"type": "凶", "desc": "惊恐不安，口舌是非"}
    }
    
    # 星吉凶
    STAR_FORTUNE = {
        "天蓬": {"type": "凶", "desc": "盗贼小人，阴谋诡计"},
        "天芮": {"type": "大凶", "desc": "疾病灾祸，破财损丁"},
        "天冲": {"type": "凶", "desc": "冲动莽撞，易生争执"},
        "天辅": {"type": "大吉", "desc": "文昌贵人，智慧辅佐"},
        "天禽": {"type": "中平", "desc": "中正平和，稳定发展"},
        "天心": {"type": "大吉", "desc": "医药治疗，心想事成"},
        "天柱": {"type": "凶", "desc": "顶梁支柱，压力重大"},
        "天任": {"type": "吉", "desc": "任劳任怨，踏实可靠"},
        "天英": {"type": "中平", "desc": "文书火光，虚名虚利"}
    }
    
    def __init__(self, year: int, month: int, day: int, hour: int, minute: int = 0):
        """初始化奇门遁甲盘"""
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.datetime = datetime(year, month, day, hour, minute)
        
        # 获取四柱
        self.year_gz = get_year_ganzhi(year)
        self.month_gz = get_month_ganzhi(year, month)
        self.day_gz = get_day_ganzhi(year, month, day)
        
        # 获取日干索引用于时柱
        day_gan = self.day_gz[0]
        tiangan = "甲乙丙丁戊己庚辛壬癸"
        day_gan_index = tiangan.index(day_gan)
        self.hour_gz = get_hour_ganzhi(day_gan_index, hour)
        
        # 确定阴阳遁和局数
        self.dun_type, self.ju_number = self._determine_dun_and_ju()
        
        # 排盘
        self.chart = self._arrange_chart()
    
    def _determine_dun_and_ju(self) -> Tuple[str, int]:
        """确定阴遁阳遁和局数"""
        # 简化版：根据节气判断
        # 冬至到夏至为阳遁，夏至到冬至为阴遁
        
        # 获取当年冬至和夏至日期
        dongzhi = get_solar_term_date(self.year, 21)  # 冬至是第22个节气（索引21）
        xiazhi = get_solar_term_date(self.year, 9)    # 夏至是第10个节气（索引9）
        
        if dongzhi <= self.datetime < xiazhi or self.datetime >= dongzhi:
            dun_type = "阳遁"
        else:
            dun_type = "阴遁"
        
        # 简化局数计算：根据日期模拟
        # 实际应该根据节气和日干支精确计算
        ju_number = ((self.month + self.day) % 9) + 1
        
        return dun_type, ju_number
    
    def _arrange_chart(self) -> Dict:
        """排盘"""
        chart = {}
        
        # 确定值符宫位（简化：根据时辰）
        zhifu_palace = (self.hour % 8) + 1
        if zhifu_palace == 5:
            zhifu_palace = 2  # 中宫寄坤二宫
        
        # 为每个宫位分配天干、八门、九星、八神
        for palace_num in [4, 9, 2, 3, 5, 7, 8, 1, 6]:
            palace_name = self.PALACES[palace_num]
            
            # 计算该宫的索引
            palace_index = palace_num - 1
            
            # 分配天干（地盘和天盘）
            dipan_gan = self.TIANGAN_ORDER[palace_index % 9]
            tianpan_gan = self.TIANGAN_ORDER[(palace_index + self.ju_number) % 9]
            
            # 分配八门
            gate = self.EIGHT_GATES[palace_index % 8]
            
            # 分配九星
            star = self.NINE_STARS[palace_index % 9]
            
            # 分配八神
            spirit = self.EIGHT_SPIRITS[palace_index % 8]
            
            chart[palace_name] = {
                "宫位": palace_name,
                "宫数": palace_num,
                "地盘": dipan_gan,
                "天盘": tianpan_gan,
                "八门": gate,
                "九星": star,
                "八神": spirit,
                "门吉凶": self.GATE_FORTUNE[gate],
                "星吉凶": self.STAR_FORTUNE[star]
            }
        
        return chart
    
    def get_chart(self) -> Dict:
        """获取完整盘面"""
        return self.chart
    
    def analyze_palace(self, palace_name: str) -> Dict:
        """分析特定宫位"""
        if palace_name not in self.chart:
            return {"error": "宫位不存在"}
        
        palace = self.chart[palace_name]
        
        # 综合吉凶判断
        gate_type = palace["门吉凶"]["type"]
        star_type = palace["星吉凶"]["type"]
        
        # 简单的吉凶评分
        fortune_score = 0
        if "大吉" in gate_type:
            fortune_score += 2
        elif "吉" in gate_type:
            fortune_score += 1
        elif "凶" in gate_type:
            fortune_score -= 1
        elif "大凶" in gate_type:
            fortune_score -= 2
        
        if "大吉" in star_type:
            fortune_score += 2
        elif "吉" in star_type:
            fortune_score += 1
        elif "凶" in star_type:
            fortune_score -= 1
        elif "大凶" in star_type:
            fortune_score -= 2
        
        if fortune_score >= 3:
            overall = "大吉"
        elif fortune_score >= 1:
            overall = "吉"
        elif fortune_score <= -3:
            overall = "大凶"
        elif fortune_score <= -1:
            overall = "凶"
        else:
            overall = "中平"
        
        return {
            "宫位": palace_name,
            "详情": palace,
            "综合吉凶": overall,
            "吉凶分数": fortune_score
        }
    
    def find_best_direction(self) -> Dict:
        """寻找最佳方位"""
        best_palace = None
        best_score = -999
        
        for palace_name, palace_data in self.chart.items():
            analysis = self.analyze_palace(palace_name)
            score = analysis["吉凶分数"]
            
            if score > best_score:
                best_score = score
                best_palace = palace_name
        
        return {
            "最佳方位": best_palace,
            "吉凶": self.analyze_palace(best_palace)["综合吉凶"],
            "详情": self.chart[best_palace]
        }
    
    def predict_matter(self, matter_type: str = "通用") -> Dict:
        """预测事情吉凶"""
        # 根据事情类型选择关键宫位
        key_palaces = {
            "求财": ["生门", "开门"],
            "求职": ["开门", "休门"],
            "婚姻": ["生门", "景门"],
            "出行": ["开门", "休门"],
            "诉讼": ["惊门", "伤门"],
            "疾病": ["死门", "伤门"],
            "学业": ["景门", "开门"],
            "通用": ["开门", "生门", "休门"]
        }
        
        target_gates = key_palaces.get(matter_type, key_palaces["通用"])
        
        # 找到对应的宫位
        relevant_palaces = []
        for palace_name, palace_data in self.chart.items():
            if palace_data["八门"] in target_gates:
                analysis = self.analyze_palace(palace_name)
                relevant_palaces.append(analysis)
        
        # 排序找最佳
        relevant_palaces.sort(key=lambda x: x["吉凶分数"], reverse=True)
        
        if relevant_palaces:
            best = relevant_palaces[0]
            return {
                "事项": matter_type,
                "最佳宫位": best["宫位"],
                "综合吉凶": best["综合吉凶"],
                "建议": self._get_advice(best["综合吉凶"], matter_type),
                "详情": best["详情"]
            }
        else:
            return {
                "事项": matter_type,
                "建议": "此时不宜进行此事，建议另择时日"
            }
    
    def _get_advice(self, fortune: str, matter_type: str) -> str:
        """根据吉凶给出建议"""
        advice_map = {
            "大吉": f"此时{matter_type}大吉，天时地利人和，可大胆行事，必有所成。",
            "吉": f"此时{matter_type}较为有利，顺势而为，稳步推进，可获成功。",
            "中平": f"此时{matter_type}平平，无大吉大凶，谨慎行事，量力而为。",
            "凶": f"此时{matter_type}不利，阻碍较多，建议暂缓或改变策略。",
            "大凶": f"此时{matter_type}大凶，万事不利，强烈建议另择吉时，切勿冒进。"
        }
        return advice_map.get(fortune, "请谨慎行事")
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "时间信息": {
                "阳历": f"{self.year}年{self.month}月{self.day}日 {self.hour}时{self.minute}分",
                "年柱": self.year_gz,
                "月柱": self.month_gz,
                "日柱": self.day_gz,
                "时柱": self.hour_gz
            },
            "遁甲信息": {
                "阴阳遁": self.dun_type,
                "局数": f"{self.ju_number}局"
            },
            "九宫盘": self.chart,
            "最佳方位": self.find_best_direction(),
            "说明": "奇门遁甲是中国最高级的预测体系，可用于预测、择时、择方、布局等"
        }


def divine_qimen(year: int, month: int, day: int, hour: int, minute: int = 0, 
                 matter_type: str = "通用") -> Dict:
    """
    奇门遁甲占卜
    
    参数:
    - year, month, day, hour, minute: 时间
    - matter_type: 事项类型（求财、求职、婚姻、出行、诉讼、疾病、学业、通用）
    
    返回: 完整的奇门遁甲分析
    """
    chart = QiMenChart(year, month, day, hour, minute)
    result = chart.to_dict()
    
    # 添加针对性预测
    result["事项预测"] = chart.predict_matter(matter_type)
    
    # 添加各方位分析
    result["八方分析"] = {}
    for palace_name in chart.chart.keys():
        if palace_name != "中宫":
            result["八方分析"][palace_name] = chart.analyze_palace(palace_name)
    
    return result


def get_current_qimen(matter_type: str = "通用") -> Dict:
    """获取当前时刻的奇门遁甲盘"""
    now = datetime.now()
    return divine_qimen(now.year, now.month, now.day, now.hour, now.minute, matter_type)
