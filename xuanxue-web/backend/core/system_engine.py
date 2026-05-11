"""
统一系统引擎
Unified consultation engine for the Xuanxue backend.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .bazi_core import BaZiChart
from .bazi_advanced import get_advanced_analysis
from .liuyao import divine
from .zeri import get_today_fortune, find_auspicious_days
from .qimen import divine_qimen
from .llm_helper import llm_helper


class UnifiedConsultRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    day: Optional[int] = Field(None, ge=1, le=31)
    hour: Optional[int] = Field(None, ge=0, le=23)
    minute: Optional[int] = Field(None, ge=0, le=59)
    gender: Optional[str] = Field(None, min_length=1, max_length=1)
    purpose: Optional[str] = Field(None, max_length=20)
    matter_type: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=80)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in ("男", "女"):
            raise ValueError("gender must be '男' or '女'")
        return value


@dataclass
class TraceStep:
    id: str
    label: str
    detail: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    rule: str = ""
    outputs: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "detail": self.detail,
            "inputs": self.inputs,
            "rule": self.rule,
            "outputs": self.outputs,
            "evidence": self.evidence,
        }


@dataclass
class TraceGraph:
    steps: List[TraceStep]
    mermaid: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": [step.to_dict() for step in self.steps],
            "mermaid": self.mermaid,
        }


MODULE_LABELS = {
    "bazi": "八字",
    "liuyao": "六爻",
    "qimen": "奇门",
    "zeri": "择日",
}


def _module_label(module_name: str) -> str:
    return MODULE_LABELS.get(module_name, module_name)


def _compact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _compact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_compact(item) for item in value]
    return value


def has_complete_birth_payload(payload: UnifiedConsultRequest) -> bool:
    return all(
        value is not None
        for value in (payload.year, payload.month, payload.day, payload.hour, payload.gender)
    )


def normalize_matter_type(question: str, preferred: Optional[str] = None) -> str:
    if preferred:
        return preferred

    text = (question or "").lower()
    keywords = {
        "求财": ["财", "赚钱", "收入", "投资", "收益", "财运", "纳财"],
        "求职": ["工作", "求职", "面试", "offer", "升职", "跳槽", "事业", "职业"],
        "婚姻": ["婚", "感情", "恋爱", "复合", "对象", "伴侣", "姻缘"],
        "出行": ["出行", "旅行", "远行", "路上", "搬动", "路程"],
        "诉讼": ["官司", "诉讼", "纠纷", "争议", "是非"],
        "疾病": ["病", "健康", "身体", "手术", "医疗", "恢复"],
        "学业": ["考试", "学习", "升学", "学业", "读书", "论文"],
    }
    for matter_type, terms in keywords.items():
        if any(term.lower() in text for term in terms):
            return matter_type
    return "通用"


def normalize_purpose(question: str, preferred: Optional[str] = None) -> str:
    if preferred:
        return preferred

    text = (question or "").lower()
    keywords = {
        "结婚": ["结婚", "嫁娶", "婚礼"],
        "开业": ["开业", "开市", "开张", "签约", "启动"],
        "搬家": ["搬家", "入宅", "移居", "乔迁"],
        "出行": ["出行", "旅行", "远行", "启程"],
        "动土": ["动土", "装修", "修造", "施工"],
        "安葬": ["安葬", "下葬", "祭祀", "追思"],
        "祈福": ["祈福", "求神", "上香", "祭拜"],
        "求财": ["求财", "纳财", "财运", "投资", "赚钱"],
    }
    for purpose, terms in keywords.items():
        if any(term.lower() in text for term in terms):
            return purpose
    return "通用"


def infer_consult_modules(question: str, has_birth: bool, matter_type: str, purpose: str) -> List[str]:
    text = (question or "").lower()
    modules: List[str] = []

    if has_birth:
        modules.append("bazi")

    liuyao_terms = [
        "能不能", "会不会", "是否", "结果", "感情", "工作", "事业", "合作", "考试", "offer",
        "面试", "复合", "辞职", "升职", "转岗", "项目", "这件事"
    ]
    qimen_terms = [
        "方向", "方位", "怎么走", "布局", "策略", "局势", "当前", "现在", "近期",
        "怎么做", "如何做", "选择", "出路", "转机"
    ]
    zeri_terms = [
        "择日", "吉日", "哪天", "日期", "时间", "开业", "结婚", "搬家", "入宅",
        "签约", "出行", "动土", "安排"
    ]

    if any(term.lower() in text for term in liuyao_terms) or matter_type in ("婚姻", "求职", "求财", "学业", "诉讼", "疾病"):
        modules.append("liuyao")

    if any(term.lower() in text for term in qimen_terms) or matter_type in ("求财", "求职", "出行", "婚姻"):
        modules.append("qimen")

    if any(term.lower() in text for term in zeri_terms) or purpose != "通用":
        modules.append("zeri")

    if not modules:
        modules = ["liuyao", "qimen"]
        if has_birth:
            modules.insert(0, "bazi")

    seen = set()
    ordered: List[str] = []
    for module in modules:
        if module not in seen:
            ordered.append(module)
            seen.add(module)
    return ordered


def summarize_bazi_result(result: Dict[str, Any]) -> Dict[str, Any]:
    analysis = result.get("analysis", {})
    advanced = result.get("advanced_analysis", {}).get("geju", {})
    strong = analysis.get("strong_element", {})
    weak = analysis.get("weak_element", {})
    return {
        "pillars": result.get("bazi", {}),
        "wuxing_count": result.get("wuxing_count", {}),
        "summary": analysis.get("wuxing_summary", ""),
        "strong_element": strong.get("element", ""),
        "weak_element": weak.get("element", ""),
        "balance_advice": analysis.get("balance_advice", ""),
        "pattern_type": advanced.get("pattern_type", ""),
        "strength_level": advanced.get("strength_level", ""),
    }


def summarize_liuyao_result(result: Dict[str, Any]) -> Dict[str, Any]:
    gua_info = result.get("gua_info", {})
    interpretation = result.get("interpretation", {})
    return {
        "question": result.get("question", ""),
        "bengua": gua_info.get("bengua", {}).get("name", ""),
        "biangua": gua_info.get("biangua", {}).get("name", ""),
        "dongyao": gua_info.get("dongyao", []),
        "summary": interpretation.get("summary", ""),
        "advice": interpretation.get("advice", ""),
        "timing": interpretation.get("timing", ""),
    }


def summarize_qimen_result(result: Dict[str, Any], matter_type: str) -> Dict[str, Any]:
    best_dir = result.get("最佳方位", {})
    matter = result.get("事项预测", {})
    time_info = result.get("时间信息", {})
    return {
        "matter_type": matter_type,
        "time": time_info.get("阳历", ""),
        "dun": result.get("遁甲信息", {}),
        "best_direction": best_dir.get("最佳方位", ""),
        "best_fortune": best_dir.get("吉凶", ""),
        "matter_fortune": matter.get("综合吉凶", ""),
        "matter_advice": matter.get("建议", ""),
    }


def summarize_zeri_result(result: Dict[str, Any], purpose: str) -> Dict[str, Any]:
    return {
        "purpose": purpose,
        "date": result.get("date", ""),
        "weekday": result.get("weekday", ""),
        "level": result.get("level", ""),
        "score": result.get("score", 0),
        "jianxing": result.get("jianxing", ""),
        "shier_shen": result.get("shier_shen", ""),
        "fortune_advice": result.get("fortune_advice", ""),
        "suitable": result.get("suitable", []),
        "avoid": result.get("avoid", []),
    }


def build_consult_context(question: str, profile: Dict[str, Any], module_summaries: Dict[str, Any]) -> str:
    pieces = [
        f"用户问题：{question}",
        f"用户档案：{json.dumps(profile, ensure_ascii=False)}",
        f"模块摘要：{json.dumps(module_summaries, ensure_ascii=False)}",
        "请整合成一份统一、审慎、可执行的玄学分析。先给总判断，再给分项依据和行动建议。",
    ]
    return "\n".join(pieces)


def fallback_consultation_summary(question: str, module_summaries: Dict[str, Any]) -> str:
    lines = [f"围绕「{question}」的系统判断如下："]
    bazi = module_summaries.get("bazi")
    if bazi:
        lines.append(f"命理底盘显示：{bazi.get('summary', '')} 建议优先参考 {bazi.get('balance_advice', '')}")
    liuyao = module_summaries.get("liuyao")
    if liuyao:
        lines.append(f"六爻提示：{liuyao.get('summary', '')} {liuyao.get('advice', '')}")
    qimen = module_summaries.get("qimen")
    if qimen:
        lines.append(f"奇门提示：{qimen.get('matter_advice', '')} 可优先考虑方位 {qimen.get('best_direction', '')}")
    zeri = module_summaries.get("zeri")
    if zeri:
        lines.append(f"择日提示：{zeri.get('level', '')}，评分 {zeri.get('score', 0)}，{zeri.get('fortune_advice', '')}")
    lines.append("总体建议：先顺着最稳定、阻力最小的路径推进，重要动作尽量与吉时、吉方和命盘优势保持一致。")
    return "\n".join(lines)


def generate_simple_analysis(chart: BaZiChart) -> dict:
    """生成简单的命理分析"""
    wuxing_count = chart.get_wuxing_count()

    max_wuxing = max(wuxing_count, key=wuxing_count.get)
    min_wuxing = min(wuxing_count, key=wuxing_count.get)

    wuxing_advice = {
        '木': {
            'strong': '木旺，性格直爽，适合从事创造性工作。注意肝胆健康。',
            'weak': '木弱，需要补木。适合多接触绿色，从事文化教育行业。'
        },
        '火': {
            'strong': '火旺，热情积极，适合从事社交、表演类工作。注意心血管健康。',
            'weak': '火弱，需要补火。适合多接触红色，从事热情洋溢的行业。'
        },
        '土': {
            'strong': '土旺，稳重踏实，适合从事管理、房地产工作。注意脾胃健康。',
            'weak': '土弱，需要补土。适合多接触黄色，从事稳定的行业。'
        },
        '金': {
            'strong': '金旺，果断坚毅，适合从事金融、技术工作。注意呼吸系统健康。',
            'weak': '金弱，需要补金。适合多接触白色，从事精密技术行业。'
        },
        '水': {
            'strong': '水旺，聪明灵活，适合从事智慧、流动性工作。注意肾脏健康。',
            'weak': '水弱，需要补水。适合多接触黑色，从事智慧型行业。'
        }
    }

    analysis = {
        'wuxing_summary': f"五行中{max_wuxing}最旺（{wuxing_count[max_wuxing]:.1f}），{min_wuxing}最弱（{wuxing_count[min_wuxing]:.1f}）",
        'strong_element': {
            'element': max_wuxing,
            'count': wuxing_count[max_wuxing],
            'advice': wuxing_advice[max_wuxing]['strong']
        },
        'weak_element': {
            'element': min_wuxing,
            'count': wuxing_count[min_wuxing],
            'advice': wuxing_advice[min_wuxing]['weak']
        },
        'balance_advice': get_balance_advice(wuxing_count),
        'disclaimer': '以上分析仅供参考，具体情况需要结合完整命盘综合判断。'
    }

    return analysis


def get_balance_advice(wuxing_count: dict) -> str:
    """根据五行平衡给出建议"""
    max_count = max(wuxing_count.values())
    min_count = min(wuxing_count.values())
    diff = max_count - min_count

    if diff < 2:
        return "五行较为平衡，命局稳定，发展较为顺利。"
    elif diff < 4:
        return "五行有一定偏颇，建议在生活中注意平衡，补足弱项。"
    else:
        return "五行偏颇较大，建议通过方位、颜色、职业等方式调整平衡。"


def build_trace_graph(
    question: str,
    modules: List[str],
    profile: Dict[str, Any],
    module_results: Dict[str, Any],
    module_summaries: Dict[str, Any],
    answer: str,
    ai_enabled: bool,
    ai_synthesized: bool,
) -> TraceGraph:
    steps: List[TraceStep] = []
    edges: List[tuple[str, str]] = []

    def add_step(
        step_id: str,
        label: str,
        detail: str,
        *,
        inputs: Optional[Dict[str, Any]] = None,
        rule: str = "",
        outputs: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[str]] = None,
        previous: Optional[str] = None,
    ) -> str:
        steps.append(
            TraceStep(
                id=step_id,
                label=label,
                detail=detail,
                inputs=_compact(inputs or {}),
                rule=rule,
                outputs=_compact(outputs or {}),
                evidence=[str(item) for item in (evidence or [])],
            )
        )
        if previous:
            edges.append((previous, step_id))
        return step_id

    last_step = add_step(
        "input",
        "输入问题",
        question,
        inputs={
            "question": question,
            "birth": profile.get("birth"),
            "gender": profile.get("gender"),
            "location": profile.get("location"),
        },
        rule="原始输入进入统一引擎",
        outputs={"question": question, "profile": profile},
    )

    last_step = add_step(
        "intent",
        "意图识别",
        f"事项：{profile.get('matter_type', '通用')}；用途：{profile.get('purpose', '通用')}",
        inputs={"question": question, "profile": profile},
        rule="根据关键词与出生信息判断事项、用途和可用模块",
        outputs={
            "matter_type": profile.get("matter_type", "通用"),
            "purpose": profile.get("purpose", "通用"),
            "modules": modules,
        },
        previous=last_step,
    )

    last_step = add_step(
        "router",
        "模块编排",
        " -> ".join(_module_label(module) for module in modules) or "未命中专门模块",
        inputs={"matter_type": profile.get("matter_type"), "purpose": profile.get("purpose")},
        rule="按问题类型路由到八字、六爻、奇门、择日子系统",
        outputs={"modules": modules},
        evidence=[f"命中模块：{_module_label(module)}" for module in modules],
        previous=last_step,
    )

    if "bazi" in modules and profile.get("birth"):
        bazi_result = module_results.get("bazi", {})
        bazi_analysis = bazi_result.get("analysis", {})
        bazi_advanced = bazi_result.get("advanced_analysis", {}).get("geju", {})
        last_step = add_step(
            "bazi_chart",
            "八字排盘",
            "四柱、五行与十神计算",
            inputs={
                "birth": profile.get("birth"),
                "gender": profile.get("gender"),
            },
            rule="以立春定年、以节气定月、以日差定日、以日干推时",
            outputs={
                "pillars": bazi_result.get("bazi", {}),
                "wuxing_count": bazi_result.get("wuxing_count", {}),
                "shishen": bazi_result.get("shishen", {}),
            },
            evidence=[
                f"年柱：{bazi_result.get('bazi', {}).get('year')}",
                f"月柱：{bazi_result.get('bazi', {}).get('month')}",
                f"日柱：{bazi_result.get('bazi', {}).get('day')}",
                f"时柱：{bazi_result.get('bazi', {}).get('hour')}",
            ],
            previous=last_step,
        )
        last_step = add_step(
            "bazi_judge",
            "八字判读",
            "身强身弱与格局判断",
            inputs={
                "pillars": bazi_result.get("bazi", {}),
                "wuxing_count": bazi_result.get("wuxing_count", {}),
            },
            rule="综合月令、地支根气、天干帮扶判断强弱，再据五行偏向定格局",
            outputs={
                "summary": bazi_analysis.get("wuxing_summary", ""),
                "strong_element": bazi_analysis.get("strong_element", {}),
                "weak_element": bazi_analysis.get("weak_element", {}),
                "balance_advice": bazi_analysis.get("balance_advice", ""),
                "pattern_type": bazi_advanced.get("pattern_type", ""),
                "strength_level": bazi_advanced.get("strength_level", ""),
            },
            evidence=[
                bazi_analysis.get("wuxing_summary", ""),
                bazi_advanced.get("pattern_description", ""),
            ],
            previous=last_step,
        )

    if "liuyao" in modules:
        liuyao_result = module_results.get("liuyao", {})
        interpretation = liuyao_result.get("interpretation", {})
        last_step = add_step(
            "liuyao_cast",
            "六爻起卦",
            "问题 -> 卦象 -> 动爻 -> 变卦",
            inputs={"question": question},
            rule="以问题为核心抽取卦象和动爻，形成问事结构",
            outputs={
                "bengua": liuyao_result.get("gua_info", {}).get("bengua", {}),
                "biangua": liuyao_result.get("gua_info", {}).get("biangua", {}),
                "dongyao": liuyao_result.get("gua_info", {}).get("dongyao", []),
            },
            evidence=[
                f"本卦：{liuyao_result.get('gua_info', {}).get('bengua', {}).get('name', '')}",
                f"变卦：{liuyao_result.get('gua_info', {}).get('biangua', {}).get('name', '')}",
            ],
            previous=last_step,
        )
        last_step = add_step(
            "liuyao_judge",
            "六爻解读",
            "卦象综合判断",
            inputs={"gua_info": liuyao_result.get("gua_info", {})},
            rule="按本卦、变卦、动爻和问题语境综合推断",
            outputs={
                "summary": interpretation.get("summary", ""),
                "advice": interpretation.get("advice", ""),
                "timing": interpretation.get("timing", ""),
            },
            evidence=[
                interpretation.get("summary", ""),
                interpretation.get("advice", ""),
            ],
            previous=last_step,
        )

    if "qimen" in modules:
        qimen_result = module_results.get("qimen", {})
        matter = qimen_result.get("事项预测", {})
        best_dir = qimen_result.get("最佳方位", {})
        last_step = add_step(
            "qimen_chart",
            "奇门排盘",
            "时间 -> 阴阳遁 -> 局数 -> 九宫",
            inputs={
                "time": qimen_result.get("时间信息", {}),
                "matter_type": profile.get("matter_type", "通用"),
            },
            rule="依据当前时空排出阴阳遁与局数，再布九宫、八门、九星、八神",
            outputs={
                "dun": qimen_result.get("遁甲信息", {}),
                "chart": qimen_result.get("九宫盘", {}),
            },
            evidence=[
                f"阴阳遁：{qimen_result.get('遁甲信息', {}).get('阴阳遁', '')}",
                f"局数：{qimen_result.get('遁甲信息', {}).get('局数', '')}",
            ],
            previous=last_step,
        )
        last_step = add_step(
            "qimen_judge",
            "奇门判断",
            "方位与事项推断",
            inputs={
                "chart": qimen_result.get("九宫盘", {}),
                "matter_type": profile.get("matter_type", "通用"),
            },
            rule="比较关键宫位的门星神组合，择出最优方位与事项结论",
            outputs={
                "best_direction": best_dir.get("最佳方位", ""),
                "best_fortune": best_dir.get("吉凶", ""),
                "matter_fortune": matter.get("综合吉凶", ""),
                "matter_advice": matter.get("建议", ""),
            },
            evidence=[
                f"最佳方位：{best_dir.get('最佳方位', '')}",
                f"事项吉凶：{matter.get('综合吉凶', '')}",
            ],
            previous=last_step,
        )

    if "zeri" in modules:
        zeri_result = module_results.get("zeri", {})
        today_fortune = zeri_result.get("today_fortune", {})
        last_step = add_step(
            "zeri_score",
            "择日评分",
            "建星、十二神、星宿、百忌综合评分",
            inputs={
                "date": today_fortune.get("date", ""),
                "purpose": profile.get("purpose", "通用"),
            },
            rule="用十二建星、十二神、星宿和彭祖百忌计算日期可用性",
            outputs={
                "level": today_fortune.get("level", ""),
                "score": today_fortune.get("score", 0),
                "jianxing": today_fortune.get("jianxing", ""),
                "shier_shen": today_fortune.get("shier_shen", ""),
                "suitable": today_fortune.get("suitable", []),
                "avoid": today_fortune.get("avoid", []),
            },
            evidence=[
                f"建星：{today_fortune.get('jianxing', '')}",
                f"十二神：{today_fortune.get('shier_shen', '')}",
                f"评分：{today_fortune.get('score', 0)}",
            ],
            previous=last_step,
        )
        if zeri_result.get("auspicious_days"):
            last_step = add_step(
                "zeri_candidates",
                "候选日期",
                "筛选出更合适的备选日",
                inputs={
                    "month": today_fortune.get("date", ""),
                    "purpose": profile.get("purpose", "通用"),
                },
                rule="对月内日期进行排序，保留分数更高且用途匹配的日期",
                outputs={"candidate_days": zeri_result.get("auspicious_days", [])},
                evidence=[item.get("date", "") for item in zeri_result.get("auspicious_days", [])],
                previous=last_step,
            )

    synthesis_input = {
        "question": question,
        "module_summaries": module_summaries,
    }
    last_step = add_step(
        "synthesis",
        "统一综合",
        "AI 综合输出" if ai_synthesized else "规则回退输出",
        inputs=synthesis_input,
        rule="把模块摘要整合成最终建议，并保留可回看证据链",
        outputs={
            "answer": answer,
            "ai": {
                "enabled": ai_enabled,
                "synthesized": ai_synthesized,
                "fallback": not ai_synthesized,
            },
        },
        evidence=[
            "模块摘要已汇总",
            "最终输出保留到 trace",
        ],
        previous=last_step,
    )

    if not ai_enabled:
        last_step = add_step(
            "fallback",
            "兼容模式",
            "后端未启用AI时，使用规则化回退输出。",
            inputs={"ai_enabled": ai_enabled},
            rule="当大模型不可用时，回退到固定模板与规则总结",
            outputs={"answer": answer},
            evidence=["AI 未启用"],
            previous=last_step,
        )

    last_step = add_step(
        "answer",
        "结果输出",
        answer,
        inputs={
            "answer": answer,
            "ai": {
                "enabled": ai_enabled,
                "synthesized": ai_synthesized,
                "fallback": not ai_synthesized,
            },
        },
        rule="把综合结果呈现给用户",
        outputs={"answer": answer},
        evidence=["最终答案已返回前端"],
        previous=last_step,
    )

    label_map = {step.id: step.label for step in steps}
    mermaid_lines = ["flowchart TD"]
    for source, target in edges:
        mermaid_lines.append(f'  {source}["{label_map.get(source, source)}"] --> {target}["{label_map.get(target, target)}"]')

    return TraceGraph(steps=steps, mermaid="\n".join(mermaid_lines))


class ConsultationEngine:
    """统一问事编排器。"""

    def consult(self, payload: UnifiedConsultRequest) -> Dict[str, Any]:
        question = payload.question.strip()
        has_birth = has_complete_birth_payload(payload)
        matter_type = normalize_matter_type(question, payload.matter_type)
        purpose = normalize_purpose(question, payload.purpose)
        modules = infer_consult_modules(question, has_birth, matter_type, purpose)

        profile = {
            "has_birth": has_birth,
            "gender": payload.gender if has_birth else None,
            "birth": {
                "year": payload.year,
                "month": payload.month,
                "day": payload.day,
                "hour": payload.hour,
                "minute": 0 if payload.minute is None else payload.minute,
            } if has_birth else None,
            "purpose": purpose,
            "matter_type": matter_type,
            "location": payload.location or "",
        }

        module_results: Dict[str, Any] = {}
        module_summaries: Dict[str, Any] = {}

        if "bazi" in modules and has_birth:
            chart = BaZiChart(
                payload.year,
                payload.month,
                payload.day,
                payload.hour,
                payload.minute or 0,
                payload.gender or "男",
            )
            bazi_result = chart.to_dict()
            bazi_result["analysis"] = generate_simple_analysis(chart)
            bazi_result["advanced_analysis"] = get_advanced_analysis(chart)
            module_results["bazi"] = bazi_result
            module_summaries["bazi"] = summarize_bazi_result(bazi_result)

        if "liuyao" in modules:
            liuyao_result = divine(question)
            if llm_helper.is_available():
                ai_interpretation = llm_helper.enhance_liuyao_interpretation(liuyao_result)
                if ai_interpretation:
                    liuyao_result["ai_interpretation"] = ai_interpretation
            module_results["liuyao"] = liuyao_result
            module_summaries["liuyao"] = summarize_liuyao_result(liuyao_result)

        if "qimen" in modules:
            now = datetime.now()
            qimen_result = divine_qimen(
                now.year,
                now.month,
                now.day,
                now.hour,
                now.minute,
                matter_type,
            )
            if llm_helper.is_available():
                ai_interpretation = llm_helper.enhance_qimen_interpretation(qimen_result, matter_type)
                if ai_interpretation:
                    qimen_result["ai_interpretation"] = ai_interpretation
            module_results["qimen"] = qimen_result
            module_summaries["qimen"] = summarize_qimen_result(qimen_result, matter_type)

        if "zeri" in modules:
            today = datetime.now()
            today_fortune = get_today_fortune(today.year, today.month, today.day)
            purpose_days = find_auspicious_days(today.year, today.month, purpose, 14) if purpose != "通用" else []
            zeri_result = {
                "today_fortune": today_fortune,
                "auspicious_days": purpose_days[:5],
            }
            if llm_helper.is_available():
                ai_advice = llm_helper.enhance_zeri_advice(today_fortune, purpose)
                if ai_advice:
                    zeri_result["ai_advice"] = ai_advice
            module_results["zeri"] = zeri_result
            module_summaries["zeri"] = summarize_zeri_result(today_fortune, purpose)
            if purpose_days:
                module_summaries["zeri"]["candidate_days"] = [
                    {
                        "date": item.get("date", ""),
                        "weekday": item.get("weekday", ""),
                        "level": item.get("level", ""),
                        "score": item.get("score", 0),
                    }
                    for item in purpose_days[:5]
                ]

        ai_enabled = llm_helper.is_available()
        synthesis_context = build_consult_context(question, profile, module_summaries)
        synthesis = llm_helper.chat(question, synthesis_context) if ai_enabled else None
        answer = synthesis or fallback_consultation_summary(question, module_summaries)
        trace = build_trace_graph(
            question=question,
            modules=modules,
            profile=profile,
            module_results=module_results,
            module_summaries=module_summaries,
            answer=answer,
            ai_enabled=ai_enabled,
            ai_synthesized=synthesis is not None,
        )

        return {
            "question": question,
            "profile": profile,
            "intent": {
                "modules": modules,
                "matter_type": matter_type,
                "purpose": purpose,
            },
            "modules": module_results,
            "module_summaries": module_summaries,
            "answer": answer,
            "trace": trace.to_dict(),
            "ai": {
                "enabled": ai_enabled,
                "synthesized": synthesis is not None,
                "fallback": synthesis is None,
            },
        }


consultation_engine = ConsultationEngine()
