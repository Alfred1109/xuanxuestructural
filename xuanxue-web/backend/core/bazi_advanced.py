"""
八字高级分析模块
Advanced BaZi Analysis Module
"""

from typing import Dict, List
from .ganzhi import get_wuxing, get_yinyang, TIANGAN, DIZHI


class BaZiAdvancedAnalysis:
    """八字高级分析类"""
    
    def __init__(self, bazi_chart):
        self.chart = bazi_chart
        self.day_gan = bazi_chart.day_pillar[0]
        self.day_zhi = bazi_chart.day_pillar[1]
        self.day_wuxing = get_wuxing(self.day_gan)
        
    def analyze_geju(self) -> Dict:
        """
        格局分析
        判断命局的格局类型
        """
        tiangan = self.chart.get_tiangan()
        dizhi = self.chart.get_dizhi()
        wuxing_count = self.chart.get_wuxing_count()
        
        # 判断身强身弱
        strength = self._calculate_strength()
        
        # 判断格局类型
        pattern_type = self._determine_pattern_type(strength, wuxing_count)
        
        return {
            'strength': strength,
            'strength_level': self._get_strength_level(strength),
            'pattern_type': pattern_type,
            'pattern_description': self._get_pattern_description(pattern_type),
            'suitable_career': self._get_suitable_career(pattern_type),
            'life_advice': self._get_life_advice(pattern_type, strength)
        }
    
    def _calculate_strength(self) -> float:
        """
        计算日主强弱
        考虑月令、地支、天干的综合影响
        """
        strength = 0.0
        
        # 1. 月令得令（最重要，占40%）
        month_zhi = self.chart.month_pillar[1]
        month_relation = self._get_wuxing_relation(self.day_wuxing, get_wuxing(month_zhi))
        
        if month_relation == '同':
            strength += 4.0  # 得令
        elif month_relation == '生我':
            strength += 3.0  # 次得令
        elif month_relation == '克我':
            strength -= 3.0  # 失令
        elif month_relation == '我克':
            strength -= 2.0
        
        # 2. 地支根气（占30%）
        for zhi in self.chart.get_dizhi():
            zhi_wuxing = get_wuxing(zhi)
            relation = self._get_wuxing_relation(self.day_wuxing, zhi_wuxing)
            if relation == '同':
                strength += 1.5
            elif relation == '生我':
                strength += 1.0
            elif relation == '克我':
                strength -= 1.0
        
        # 3. 天干帮扶（占30%）
        for gan in self.chart.get_tiangan():
            if gan == self.day_gan:
                continue
            gan_wuxing = get_wuxing(gan)
            relation = self._get_wuxing_relation(self.day_wuxing, gan_wuxing)
            if relation == '同':
                strength += 1.0
            elif relation == '生我':
                strength += 0.8
            elif relation == '克我':
                strength -= 0.8
        
        return strength
    
    def _get_wuxing_relation(self, my_wuxing: str, other_wuxing: str) -> str:
        """判断五行关系"""
        relations = {
            '木': {'木': '同', '火': '我生', '土': '我克', '金': '克我', '水': '生我'},
            '火': {'火': '同', '土': '我生', '金': '我克', '水': '克我', '木': '生我'},
            '土': {'土': '同', '金': '我生', '水': '我克', '木': '克我', '火': '生我'},
            '金': {'金': '同', '水': '我生', '木': '我克', '火': '克我', '土': '生我'},
            '水': {'水': '同', '木': '我生', '火': '我克', '土': '克我', '金': '生我'}
        }
        return relations.get(my_wuxing, {}).get(other_wuxing, '未知')
    
    def _get_strength_level(self, strength: float) -> str:
        """获取强弱等级"""
        if strength >= 5:
            return '极旺'
        elif strength >= 2:
            return '偏旺'
        elif strength >= -2:
            return '中和'
        elif strength >= -5:
            return '偏弱'
        else:
            return '极弱'
    
    def _determine_pattern_type(self, strength: float, wuxing_count: Dict) -> str:
        """判断格局类型"""
        if strength >= 5:
            return '从强格'
        elif strength <= -5:
            return '从弱格'
        elif -2 <= strength <= 2:
            # 中和格局，看用神
            max_wuxing = max(wuxing_count, key=wuxing_count.get)
            if max_wuxing == self.day_wuxing:
                return '比劫格'
            else:
                relation = self._get_wuxing_relation(self.day_wuxing, max_wuxing)
                if relation == '我生':
                    return '食伤格'
                elif relation == '我克':
                    return '财格'
                elif relation == '克我':
                    return '官杀格'
                elif relation == '生我':
                    return '印格'
        elif strength > 2:
            return '身旺格'
        else:
            return '身弱格'
        
        return '普通格局'
    
    def _get_pattern_description(self, pattern: str) -> str:
        """获取格局描述"""
        descriptions = {
            '从强格': '命局极旺，宜顺势而为，发挥自身优势，适合创业、领导等强势行业。',
            '从弱格': '命局极弱，宜以柔克刚，借助外力，适合辅助、服务类工作。',
            '身旺格': '日主偏旺，精力充沛，行动力强，但需注意控制情绪，避免冲动。',
            '身弱格': '日主偏弱，需要贵人扶持，宜稳扎稳打，循序渐进发展。',
            '比劫格': '兄弟朋友多助力，适合合作事业，但需注意财务管理。',
            '食伤格': '才华横溢，创意丰富，适合艺术、设计、创作类工作。',
            '财格': '财运亨通，善于理财，适合商业、金融、投资类工作。',
            '官杀格': '事业心强，有管理才能，适合公职、管理、执法类工作。',
            '印格': '学习能力强，有文化修养，适合教育、研究、文化类工作。',
            '普通格局': '命局平和，各方面较为均衡，发展方向多样。'
        }
        return descriptions.get(pattern, '命局特殊，需要综合分析。')
    
    def _get_suitable_career(self, pattern: str) -> List[str]:
        """根据格局推荐适合的职业"""
        careers = {
            '从强格': ['企业家', '高管', '政治家', '军人', '运动员'],
            '从弱格': ['顾问', '助理', '客服', '护理', '服务业'],
            '身旺格': ['销售', '市场', '公关', '演艺', '体育'],
            '身弱格': ['技术', '研发', '设计', '文案', '后勤'],
            '比劫格': ['合伙生意', '团队管理', '社交媒体', '人力资源'],
            '食伤格': ['艺术家', '设计师', '作家', '演员', '创意总监'],
            '财格': ['金融', '投资', '贸易', '房地产', '商业'],
            '官杀格': ['公务员', '法官', '警察', '经理', '主管'],
            '印格': ['教师', '学者', '研究员', '编辑', '文化工作者'],
            '普通格局': ['根据个人兴趣和专长选择']
        }
        return careers.get(pattern, ['多方面尝试，找到适合自己的方向'])
    
    def _get_life_advice(self, pattern: str, strength: float) -> str:
        """根据格局和强弱给出人生建议"""
        if strength > 3:
            return '您的命局偏旺，精力充沛，行动力强。建议：1) 发挥主动性，勇于开拓；2) 注意控制脾气，避免冲动；3) 多从事消耗精力的活动；4) 学会倾听他人意见。'
        elif strength < -3:
            return '您的命局偏弱，需要外力扶持。建议：1) 寻找贵人相助；2) 稳扎稳打，不要冒进；3) 注重养生保健；4) 多学习充实自己；5) 选择有靠山的环境发展。'
        else:
            return '您的命局较为平衡，发展稳定。建议：1) 保持现有优势；2) 适度进取；3) 注意五行平衡；4) 根据流年调整策略。'
    
    def analyze_shensha(self) -> Dict:
        """
        神煞分析
        分析命局中的吉凶神煞
        """
        year_zhi = self.chart.year_pillar[1]
        day_zhi = self.chart.day_pillar[1]
        
        shensha_list = []
        
        # 桃花（子午卯酉）
        taohua_map = {
            '寅': '卯', '午': '卯', '戌': '卯',  # 寅午戌见卯
            '申': '酉', '子': '酉', '辰': '酉',  # 申子辰见酉
            '巳': '午', '酉': '午', '丑': '午',  # 巳酉丑见午
            '亥': '子', '卯': '子', '未': '子'   # 亥卯未见子
        }
        
        for zhi in self.chart.get_dizhi():
            if zhi in ['子', '午', '卯', '酉']:
                expected = taohua_map.get(year_zhi)
                if zhi == expected:
                    shensha_list.append({
                        'name': '桃花',
                        'type': '吉',
                        'description': '主人缘好，异性缘佳，有艺术天赋，但需注意感情问题。'
                    })
                    break
        
        # 驿马（寅申巳亥）
        yima_map = {
            '寅': '申', '午': '寅', '戌': '寅',
            '申': '寅', '子': '寅', '辰': '寅',
            '巳': '亥', '酉': '巳', '丑': '巳',
            '亥': '巳', '卯': '亥', '未': '亥'
        }
        
        for zhi in self.chart.get_dizhi():
            expected = yima_map.get(year_zhi)
            if zhi == expected:
                shensha_list.append({
                    'name': '驿马',
                    'type': '吉',
                    'description': '主奔波走动，适合外出发展，从事流动性工作。'
                })
                break
        
        # 华盖
        huagai_map = {
            '寅': '戌', '午': '戌', '戌': '戌',
            '申': '辰', '子': '辰', '辰': '辰',
            '巳': '丑', '酉': '丑', '丑': '丑',
            '亥': '未', '卯': '未', '未': '未'
        }
        
        for zhi in self.chart.get_dizhi():
            expected = huagai_map.get(year_zhi)
            if zhi == expected:
                shensha_list.append({
                    'name': '华盖',
                    'type': '吉',
                    'description': '主聪明好学，有艺术天赋，喜欢玄学宗教，性格孤傲。'
                })
                break
        
        # 天乙贵人
        tianyiguiren_map = {
            '甲': ['丑', '未'], '戊': ['丑', '未'],
            '乙': ['子', '申'], '己': ['子', '申'],
            '丙': ['亥', '酉'], '丁': ['亥', '酉'],
            '庚': ['丑', '未'], '辛': ['寅', '午'],
            '壬': ['卯', '巳'], '癸': ['卯', '巳']
        }
        
        day_gan = self.chart.day_pillar[0]
        guiren_zhi = tianyiguiren_map.get(day_gan, [])
        for zhi in self.chart.get_dizhi():
            if zhi in guiren_zhi:
                shensha_list.append({
                    'name': '天乙贵人',
                    'type': '大吉',
                    'description': '遇难呈祥，逢凶化吉，一生多贵人相助。'
                })
                break
        
        return {
            'shensha_list': shensha_list,
            'shensha_count': len(shensha_list),
            'summary': f'命局中有{len(shensha_list)}个重要神煞' if shensha_list else '命局中暂无明显神煞'
        }
    
    def analyze_liuqin(self) -> Dict:
        """
        六亲分析
        分析父母、兄弟、配偶、子女关系
        """
        shishen = self.chart.get_shishen()
        
        # 根据十神判断六亲关系
        liuqin_analysis = {
            'father': self._analyze_father(shishen),
            'mother': self._analyze_mother(shishen),
            'siblings': self._analyze_siblings(shishen),
            'spouse': self._analyze_spouse(shishen),
            'children': self._analyze_children(shishen)
        }
        
        return liuqin_analysis
    
    def _analyze_father(self, shishen: Dict) -> str:
        """分析父亲关系"""
        # 偏财代表父亲
        if '偏财' in str(shishen.values()):
            return '与父亲关系较好，父亲对您有帮助。'
        return '父亲缘分一般，需要主动维系关系。'
    
    def _analyze_mother(self, shishen: Dict) -> str:
        """分析母亲关系"""
        # 正印代表母亲
        if '正印' in str(shishen.values()):
            return '与母亲关系亲密，母亲对您关爱有加。'
        return '母亲缘分一般，但仍有母爱呵护。'
    
    def _analyze_siblings(self, shishen: Dict) -> str:
        """分析兄弟姐妹关系"""
        # 比肩劫财代表兄弟姐妹
        if '比肩' in str(shishen.values()) or '劫财' in str(shishen.values()):
            return '兄弟姐妹缘分深，互相帮助，但也可能有竞争。'
        return '兄弟姐妹缘分较浅，各自发展。'
    
    def _analyze_spouse(self, shishen: Dict) -> str:
        """分析配偶关系"""
        gender = self.chart.gender
        if gender == '男':
            # 男命看财星
            if '正财' in str(shishen.values()):
                return '婚姻稳定，配偶贤惠顾家，夫妻关系和睦。'
            elif '偏财' in str(shishen.values()):
                return '异性缘好，但需注意专一，避免感情波折。'
        else:
            # 女命看官星
            if '正官' in str(shishen.values()):
                return '婚姻美满，配偶有责任心，家庭和谐。'
            elif '七杀' in str(shishen.values()):
                return '配偶性格强势，需要互相理解包容。'
        return '婚姻缘分需要经营，注重沟通和理解。'
    
    def _analyze_children(self, shishen: Dict) -> str:
        """分析子女关系"""
        # 食伤代表子女
        if '食神' in str(shishen.values()) or '伤官' in str(shishen.values()):
            return '子女聪明伶俐，有才华，亲子关系融洽。'
        return '子女缘分正常，需要用心培养。'


def get_advanced_analysis(bazi_chart) -> Dict:
    """获取完整的高级分析"""
    analyzer = BaZiAdvancedAnalysis(bazi_chart)
    
    return {
        'geju': analyzer.analyze_geju(),
        'shensha': analyzer.analyze_shensha(),
        'liuqin': analyzer.analyze_liuqin()
    }
