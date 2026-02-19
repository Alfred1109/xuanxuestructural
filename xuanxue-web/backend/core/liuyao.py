"""
六爻占卜模块
Liu Yao Divination Module
"""

import random
from datetime import datetime
from typing import Dict, List, Tuple


# 八卦基本信息
BAGUA = {
    '乾': {'binary': '111', 'wuxing': '金', 'nature': '天', 'symbol': '☰'},
    '兑': {'binary': '011', 'wuxing': '金', 'nature': '泽', 'symbol': '☱'},
    '离': {'binary': '101', 'wuxing': '火', 'nature': '火', 'symbol': '☲'},
    '震': {'binary': '001', 'wuxing': '木', 'nature': '雷', 'symbol': '☳'},
    '巽': {'binary': '110', 'wuxing': '木', 'nature': '风', 'symbol': '☴'},
    '坎': {'binary': '010', 'wuxing': '水', 'nature': '水', 'symbol': '☵'},
    '艮': {'binary': '100', 'wuxing': '土', 'nature': '山', 'symbol': '☶'},
    '坤': {'binary': '000', 'wuxing': '土', 'nature': '地', 'symbol': '☷'}
}

# 六十四卦名称
LIUSHISI_GUA = {
    '111111': '乾为天', '000000': '坤为地', '010001': '水雷屯', '100010': '山水蒙',
    '010111': '水天需', '111010': '天水讼', '000010': '地水师', '010000': '水地比',
    '110111': '风天小畜', '111011': '天泽履', '000111': '地天泰', '111000': '天地否',
    '111101': '天火同人', '101111': '火天大有', '000100': '地山谦', '001000': '雷地豫',
    '011001': '泽雷随', '100110': '山风蛊', '000011': '地泽临', '110000': '风地观',
    '101001': '火雷噬嗑', '100101': '山火贲', '100000': '山地剥', '000001': '地雷复',
    '111001': '天雷无妄', '100111': '山天大畜', '100001': '山雷颐', '011110': '泽风大过',
    '010010': '坎为水', '101101': '离为火', '011100': '泽山咸', '001110': '雷风恒',
    '111100': '天山遁', '001111': '雷天大壮', '101000': '火地晋', '000101': '地火明夷',
    '110101': '风火家人', '101011': '火泽睽', '010100': '水山蹇', '001010': '雷水解',
    '100011': '山泽损', '110001': '风雷益', '011111': '泽天夬', '111110': '天风姤',
    '011000': '泽地萃', '000110': '地风升', '011010': '泽水困', '010110': '水风井',
    '011101': '泽火革', '101110': '火风鼎', '001001': '震为雷', '100100': '艮为山',
    '110100': '风山渐', '001011': '雷泽归妹', '001101': '雷火丰', '101100': '火山旅',
    '110110': '巽为风', '011011': '兑为泽', '110010': '风水涣', '010011': '水泽节',
    '110011': '风泽中孚', '001100': '雷山小过', '010101': '水火既济', '101010': '火水未济'
}

# 六亲关系
LIUQIN_MAP = {
    ('金', '金'): '兄弟', ('金', '木'): '妻财', ('金', '水'): '子孙',
    ('金', '火'): '官鬼', ('金', '土'): '父母',
    ('木', '木'): '兄弟', ('木', '土'): '妻财', ('木', '火'): '子孙',
    ('木', '金'): '官鬼', ('木', '水'): '父母',
    ('水', '水'): '兄弟', ('水', '火'): '妻财', ('水', '木'): '子孙',
    ('水', '土'): '官鬼', ('水', '金'): '父母',
    ('火', '火'): '兄弟', ('火', '金'): '妻财', ('火', '土'): '子孙',
    ('火', '水'): '官鬼', ('火', '木'): '父母',
    ('土', '土'): '兄弟', ('土', '水'): '妻财', ('土', '金'): '子孙',
    ('土', '木'): '官鬼', ('土', '火'): '父母'
}


class LiuYaoDivination:
    """六爻占卜类"""
    
    def __init__(self, question: str = ""):
        self.question = question
        self.yao_list = []
        self.bengua = None  # 本卦
        self.biangua = None  # 变卦
        self.dongyao = []  # 动爻
        
    def cast_coins(self) -> List[int]:
        """
        摇卦（模拟投掷三枚铜钱）
        正面为3，反面为2
        三个正面（老阳）= 9 → 动爻，阳变阴
        三个反面（老阴）= 6 → 动爻，阴变阳
        两正一反（少阳）= 7 → 静爻，阳
        两反一正（少阴）= 8 → 静爻，阴
        """
        yao_list = []
        for i in range(6):
            # 模拟投掷三枚铜钱
            coins = [random.choice([2, 3]) for _ in range(3)]
            total = sum(coins)
            yao_list.append(total)
        
        self.yao_list = yao_list
        return yao_list
    
    def parse_gua(self) -> Dict:
        """解析卦象"""
        # 转换为二进制（阳爻为1，阴爻为0）
        bengua_binary = ''
        biangua_binary = ''
        dongyao = []
        
        for i, yao in enumerate(self.yao_list):
            if yao in [7, 9]:  # 阳爻
                bengua_binary += '1'
                if yao == 9:  # 老阳，动爻
                    biangua_binary += '0'
                    dongyao.append(i + 1)
                else:
                    biangua_binary += '1'
            else:  # 阴爻
                bengua_binary += '0'
                if yao == 6:  # 老阴，动爻
                    biangua_binary += '1'
                    dongyao.append(i + 1)
                else:
                    biangua_binary += '0'
        
        self.dongyao = dongyao
        
        # 获取卦名
        bengua_name = LIUSHISI_GUA.get(bengua_binary, '未知卦')
        biangua_name = LIUSHISI_GUA.get(biangua_binary, '未知卦') if dongyao else '无变卦'
        
        # 分析上下卦
        shang_gua = self._get_trigram(bengua_binary[3:])
        xia_gua = self._get_trigram(bengua_binary[:3])
        
        return {
            'bengua': {
                'name': bengua_name,
                'binary': bengua_binary,
                'shang_gua': shang_gua,
                'xia_gua': xia_gua
            },
            'biangua': {
                'name': biangua_name,
                'binary': biangua_binary
            },
            'dongyao': dongyao,
            'yao_details': self._get_yao_details(bengua_binary, dongyao)
        }
    
    def _get_trigram(self, binary: str) -> Dict:
        """根据二进制获取八卦信息"""
        for name, info in BAGUA.items():
            if info['binary'] == binary:
                return {
                    'name': name,
                    'wuxing': info['wuxing'],
                    'nature': info['nature'],
                    'symbol': info['symbol']
                }
        return {'name': '未知', 'wuxing': '未知', 'nature': '未知', 'symbol': '?'}
    
    def _get_yao_details(self, binary: str, dongyao: List[int]) -> List[Dict]:
        """获取每一爻的详细信息"""
        yao_names = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
        details = []
        
        # 获取卦的五行属性（以下卦为主）
        xia_gua_wuxing = self._get_trigram(binary[:3])['wuxing']
        
        for i, bit in enumerate(binary):
            yao_type = '阳爻' if bit == '1' else '阴爻'
            is_dong = (i + 1) in dongyao
            
            # 简化的五行配置（实际应该更复杂）
            yao_wuxing = self._get_yao_wuxing(i, xia_gua_wuxing)
            
            details.append({
                'position': i + 1,
                'name': yao_names[i],
                'type': yao_type,
                'is_dong': is_dong,
                'wuxing': yao_wuxing,
                'status': '动爻' if is_dong else '静爻'
            })
        
        return details
    
    def _get_yao_wuxing(self, position: int, base_wuxing: str) -> str:
        """获取爻的五行属性（简化版）"""
        # 这是一个简化的实现，实际应该根据纳甲法
        wuxing_cycle = ['木', '火', '土', '金', '水']
        base_index = wuxing_cycle.index(base_wuxing)
        return wuxing_cycle[(base_index + position) % 5]
    
    def interpret(self) -> Dict:
        """解卦"""
        gua_info = self.parse_gua()
        
        # 基本解释
        interpretation = {
            'summary': self._get_gua_summary(gua_info['bengua']['name']),
            'detailed': self._get_detailed_interpretation(gua_info),
            'advice': self._get_advice(gua_info),
            'timing': self._get_timing_prediction(gua_info)
        }
        
        return {
            'question': self.question,
            'gua_info': gua_info,
            'interpretation': interpretation
        }
    
    def _get_gua_summary(self, gua_name: str) -> str:
        """获取卦象的基本含义"""
        summaries = {
            '乾为天': '大吉大利，刚健有力，事业亨通，但需防骄傲自满。',
            '坤为地': '柔顺承载，厚德载物，宜守不宜攻，以静制动。',
            '水雷屯': '初始艰难，需要积累，不宜冒进，耐心等待时机。',
            '山水蒙': '蒙昧未开，需要学习，虚心求教，逐步成长。',
            '水天需': '等待时机，需要耐心，时机未到，不可强求。',
            '天水讼': '争讼之象，避免冲突，和为贵，退一步海阔天空。',
            '地水师': '众人之力，团队合作，需要领导，统筹规划。',
            '水地比': '亲密合作，互相帮助，团结一致，共同进步。'
        }
        return summaries.get(gua_name, '此卦需要综合分析，建议咨询专业人士。')
    
    def _get_detailed_interpretation(self, gua_info: Dict) -> str:
        """详细解释"""
        bengua = gua_info['bengua']
        dongyao = gua_info['dongyao']
        
        interpretation = f"本卦为{bengua['name']}，上卦{bengua['shang_gua']['name']}（{bengua['shang_gua']['nature']}），下卦{bengua['xia_gua']['name']}（{bengua['xia_gua']['nature']}）。"
        
        if dongyao:
            interpretation += f"\n动爻在第{', '.join(map(str, dongyao))}爻，表示事情正在变化之中。"
        else:
            interpretation += "\n无动爻，表示事情相对稳定，短期内不会有大的变化。"
        
        return interpretation
    
    def _get_advice(self, gua_info: Dict) -> str:
        """给出建议"""
        dongyao_count = len(gua_info['dongyao'])
        
        if dongyao_count == 0:
            return "事情稳定，保持现状即可，不宜轻举妄动。"
        elif dongyao_count == 1:
            return "有一个变数，需要关注这个变化点，适时调整策略。"
        elif dongyao_count == 2:
            return "变化较多，需要灵活应对，把握主要矛盾。"
        elif dongyao_count >= 3:
            return "变化剧烈，局势复杂，建议谨慎行事，多方咨询。"
        
        return "综合考虑各方面因素，做出明智决策。"
    
    def _get_timing_prediction(self, gua_info: Dict) -> str:
        """时间预测"""
        dongyao = gua_info['dongyao']
        
        if not dongyao:
            return "短期内（1-3个月）不会有明显变化。"
        elif max(dongyao) <= 3:
            return "变化较快，可能在近期（1-2周）就会有结果。"
        else:
            return "需要一定时间，预计1-3个月内会有明显进展。"


def divine(question: str = "", use_time: bool = False) -> Dict:
    """
    进行六爻占卜
    
    Args:
        question: 占卜的问题
        use_time: 是否使用时间起卦（暂未实现）
    
    Returns:
        占卜结果
    """
    divination = LiuYaoDivination(question)
    divination.cast_coins()
    result = divination.interpret()
    
    # 添加时间戳
    result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return result


if __name__ == "__main__":
    # 测试
    print("=== 六爻占卜测试 ===\n")
    result = divine("测试事业运势")
    
    print(f"问题：{result['question']}")
    print(f"时间：{result['timestamp']}\n")
    
    gua = result['gua_info']
    print(f"本卦：{gua['bengua']['name']}")
    print(f"变卦：{gua['biangua']['name']}")
    print(f"动爻：{gua['dongyao']}\n")
    
    interp = result['interpretation']
    print(f"卦象解释：{interp['summary']}\n")
    print(f"详细分析：{interp['detailed']}\n")
    print(f"建议：{interp['advice']}\n")
    print(f"时间：{interp['timing']}")
