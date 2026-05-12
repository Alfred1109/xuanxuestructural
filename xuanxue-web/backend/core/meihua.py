"""
梅花易数核心模块
Mei Hua Yi Shu Core Engine
"""

from datetime import datetime
from typing import Dict, List, Optional

from .liuyao import BAGUA, LIUSHISI_GUA


MEIHUA_TRIGRAM_ORDER = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤']
MEIHUA_TRIGRAM_INDEX = {name: index + 1 for index, name in enumerate(MEIHUA_TRIGRAM_ORDER)}

WUXING_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WUXING_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}


class MeiHuaDivination:
    """梅花易数占断。"""

    def __init__(
        self,
        question: str = "",
        method: str = "time",
        numbers: Optional[List[int]] = None,
        divination_time: Optional[datetime] = None,
    ):
        self.question = question.strip()
        self.method = method
        self.numbers = [int(value) for value in (numbers or [])]
        self.divination_time = divination_time or datetime.now()

    @staticmethod
    def _normalize_mod(value: int, base: int) -> int:
        remainder = value % base
        return base if remainder == 0 else remainder

    @staticmethod
    def _trigram_name(index: int) -> str:
        normalized = MeiHuaDivination._normalize_mod(index, 8)
        return MEIHUA_TRIGRAM_ORDER[normalized - 1]

    @staticmethod
    def _binary_to_name(binary: str) -> str:
        return LIUSHISI_GUA.get(binary, '未知卦')

    @staticmethod
    def _compose_gua(upper_name: str, lower_name: str) -> Dict:
        upper = BAGUA[upper_name]
        lower = BAGUA[lower_name]
        binary = lower['binary'] + upper['binary']
        return {
            'name': MeiHuaDivination._binary_to_name(binary),
            'binary': binary,
            'upper': {
                'name': upper_name,
                'wuxing': upper['wuxing'],
                'nature': upper['nature'],
                'symbol': upper['symbol'],
                'index': MEIHUA_TRIGRAM_INDEX[upper_name],
            },
            'lower': {
                'name': lower_name,
                'wuxing': lower['wuxing'],
                'nature': lower['nature'],
                'symbol': lower['symbol'],
                'index': MEIHUA_TRIGRAM_INDEX[lower_name],
            },
        }

    @staticmethod
    def _flip_line(binary: str, moving_line: int) -> str:
        chars = list(binary)
        index = moving_line - 1
        chars[index] = '0' if chars[index] == '1' else '1'
        return ''.join(chars)

    @staticmethod
    def _binary_to_trigram_names(binary: str) -> Dict[str, str]:
        lower_binary = binary[:3]
        upper_binary = binary[3:]
        lower_name = next((name for name, info in BAGUA.items() if info['binary'] == lower_binary), '未知')
        upper_name = next((name for name, info in BAGUA.items() if info['binary'] == upper_binary), '未知')
        return {'lower': lower_name, 'upper': upper_name}

    def _build_base_numbers(self) -> Dict:
        if self.method == "number":
            source_numbers = self.numbers[:3]
            if len(source_numbers) < 2:
                raise ValueError("数字起卦至少需要 2 个数字")
            upper_source = source_numbers[0]
            lower_source = source_numbers[1]
            moving_source = sum(source_numbers)
            return {
                'method': 'number',
                'source': source_numbers,
                'upper_source': upper_source,
                'lower_source': lower_source,
                'moving_source': moving_source,
            }

        now = self.divination_time
        upper_source = now.year + now.month + now.day
        lower_source = upper_source + now.hour
        moving_source = lower_source + (now.minute or 0)
        return {
            'method': 'time',
            'source': {
                'year': now.year,
                'month': now.month,
                'day': now.day,
                'hour': now.hour,
                'minute': now.minute,
            },
            'upper_source': upper_source,
            'lower_source': lower_source,
            'moving_source': moving_source,
        }

    def _get_hugua(self, bengua_binary: str) -> Dict:
        lower_name = next((name for name, info in BAGUA.items() if info['binary'] == bengua_binary[1:4]), '未知')
        upper_name = next((name for name, info in BAGUA.items() if info['binary'] == bengua_binary[2:5]), '未知')
        return self._compose_gua(upper_name, lower_name)

    def _judge_tiyong(self, bengua: Dict) -> Dict:
        lower = bengua['lower']
        upper = bengua['upper']
        lower_wuxing = lower['wuxing']
        upper_wuxing = upper['wuxing']

        if lower_wuxing == upper_wuxing:
            relation = '比和'
            summary = '体用同气，事情整体一致，阻力较小。'
        elif WUXING_SHENG[lower_wuxing] == upper_wuxing:
            relation = '体生用'
            summary = '体生用，自己付出较多，成事但较耗力。'
        elif WUXING_SHENG[upper_wuxing] == lower_wuxing:
            relation = '用生体'
            summary = '用生体，外部条件反过来帮助自己，较为有利。'
        elif WUXING_KE[lower_wuxing] == upper_wuxing:
            relation = '体克用'
            summary = '体克用，自己能掌控局面，但推进需要主动。'
        else:
            relation = '用克体'
            summary = '用克体，外部压力更强，宜谨慎应对。'

        return {
            'ti': {
                'name': lower['name'],
                'wuxing': lower_wuxing,
                'nature': lower['nature'],
            },
            'yong': {
                'name': upper['name'],
                'wuxing': upper_wuxing,
                'nature': upper['nature'],
            },
            'relation': relation,
            'summary': summary,
        }

    def divine(self) -> Dict:
        bases = self._build_base_numbers()
        upper_index = self._normalize_mod(bases['upper_source'], 8)
        lower_index = self._normalize_mod(bases['lower_source'], 8)
        moving_line = self._normalize_mod(bases['moving_source'], 6)

        upper_name = self._trigram_name(upper_index)
        lower_name = self._trigram_name(lower_index)

        bengua = self._compose_gua(upper_name, lower_name)
        hugua = self._get_hugua(bengua['binary'])
        biangua_binary = self._flip_line(bengua['binary'], moving_line)
        changed = self._binary_to_trigram_names(biangua_binary)
        biangua = self._compose_gua(changed['upper'], changed['lower'])
        tiyong = self._judge_tiyong(bengua)

        summary = f"本卦为{bengua['name']}，互卦为{hugua['name']}，动爻在第{moving_line}爻，变卦为{biangua['name']}。"
        advice = tiyong['summary']
        timing = (
            "动爻在下卦，事态变化偏快，可先看近 3-7 天。"
            if moving_line <= 3
            else "动爻在上卦，事态变化偏后，可观察 1-4 周。"
        )

        return {
            'question': self.question,
            'method': self.method,
            'timestamp': self.divination_time.strftime('%Y-%m-%d %H:%M:%S'),
            'gua_info': {
                'bengua': bengua,
                'hugua': hugua,
                'biangua': biangua,
                'moving_line': moving_line,
                'tiyong': tiyong,
            },
            'interpretation': {
                'summary': summary,
                'advice': advice,
                'timing': timing,
            },
            'calc_trace': {
                'source': bases,
                'indexes': {
                    'upper_index': upper_index,
                    'lower_index': lower_index,
                    'moving_line': moving_line,
                    'formula': [
                        f"上卦序数 = {bases['upper_source']} % 8 => {upper_index}",
                        f"下卦序数 = {bases['lower_source']} % 8 => {lower_index}",
                        f"动爻 = {bases['moving_source']} % 6 => {moving_line}",
                    ],
                },
                'bengua': {
                    'upper_name': upper_name,
                    'lower_name': lower_name,
                    'binary': bengua['binary'],
                    'result': bengua['name'],
                },
                'hugua': {
                    'formula': f"互卦下卦取本卦 2-4 爻：{bengua['binary'][1:4]}；上卦取本卦 3-5 爻：{bengua['binary'][2:5]}",
                    'binary': hugua['binary'],
                    'result': hugua['name'],
                },
                'biangua': {
                    'formula': f"第 {moving_line} 爻变位：{bengua['binary']} -> {biangua_binary}",
                    'binary': biangua_binary,
                    'result': biangua['name'],
                },
                'tiyong': tiyong,
            },
        }


def divine_meihua(
    question: str = "",
    method: str = "time",
    numbers: Optional[List[int]] = None,
    divination_time: Optional[datetime] = None,
) -> Dict:
    divination = MeiHuaDivination(
        question=question,
        method=method,
        numbers=numbers,
        divination_time=divination_time,
    )
    return divination.divine()
