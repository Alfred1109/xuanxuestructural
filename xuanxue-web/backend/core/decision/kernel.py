"""
决策内核
Transforms multi-module summaries into a unified decision world model.
"""

from typing import Any, Dict, List

from .arbitration import arbitrate_signals
from .environment_modifiers import apply_environment_modifiers, build_environment_modifiers
from .signal_schema import ModuleSignal, UnifiedEnergyVector


def infer_decision_type(question: str, profile: Dict[str, Any]) -> str:
    text = (question or "").lower()
    purpose = profile.get("purpose", "通用")
    if purpose != "通用" or any(term in text for term in ["哪天", "何时", "择日", "时间", "签约", "开业"]):
        return "temporal"
    if profile.get("has_birth") or any(term in text for term in ["事业", "人生", "长期", "发展", "方向"]):
        return "strategic"
    if any(term in text for term in ["现在", "刚刚", "马上", "这次", "合作", "谈判", "能成吗"]):
        return "tactical"
    return "balanced"


def _direction_from_text(text: str, positive_terms: List[str], negative_terms: List[str]) -> float:
    content = text or ""
    positive = sum(1 for term in positive_terms if term in content)
    negative = sum(1 for term in negative_terms if term in content)
    if positive == negative == 0:
        return 0.0
    return max(-1.0, min(1.0, (positive - negative) / max(1, positive + negative)))


def signal_from_bazi(summary: Dict[str, Any]) -> ModuleSignal:
    counts = summary.get("wuxing_count", {}) or {}
    max_value = max(counts.values()) if counts else 0
    min_value = min(counts.values()) if counts else 0
    imbalance = (max_value - min_value) * 8
    baseline = max(35.0, min(85.0, 78.0 - imbalance))
    direction = 0.2 if "平衡" in (summary.get("balance_advice", "") or "") else 0.05
    return ModuleSignal(
        module="bazi",
        layer="baseline",
        baseline_strength=baseline,
        timing_window=48.0,
        external_support=52.0,
        internal_resistance=min(80.0, 25.0 + imbalance),
        risk_exposure=min(85.0, 30.0 + imbalance),
        certainty=78.0,
        actionability=58.0,
        direction_score=direction,
        rationale=[
            summary.get("summary", ""),
            summary.get("balance_advice", ""),
        ],
        raw=summary,
    )


def signal_from_ziwei(summary: Dict[str, Any]) -> ModuleSignal:
    stars = summary.get("major_stars", []) or []
    star_density = min(4, len([item for item in stars if item])) / 4
    baseline = 60.0 + star_density * 18.0
    direction = 0.2 if "稳" in (summary.get("career_vector", "") or "") else 0.05
    return ModuleSignal(
        module="ziwei",
        layer="baseline",
        baseline_strength=baseline,
        timing_window=52.0,
        external_support=66.0,
        internal_resistance=38.0,
        risk_exposure=36.0,
        certainty=74.0,
        actionability=56.0,
        direction_score=direction,
        rationale=[
            summary.get("summary", ""),
            summary.get("career_vector", ""),
            summary.get("advice", ""),
        ],
        raw=summary,
    )


def signal_from_fengshui(summary: Dict[str, Any]) -> ModuleSignal:
    support = float(summary.get("space_support", 50) or 50)
    risk = float(summary.get("layout_risk", 50) or 50)
    direction = max(-1.0, min(1.0, (support - risk) / 100))
    return ModuleSignal(
        module="fengshui",
        layer="space",
        baseline_strength=54.0,
        timing_window=50.0,
        external_support=support,
        internal_resistance=max(20.0, 85.0 - support),
        risk_exposure=risk,
        certainty=68.0,
        actionability=62.0,
        direction_score=direction,
        rationale=[
            summary.get("summary", ""),
            summary.get("adjustment_advice", ""),
        ],
        raw=summary,
    )


def signal_from_liuyao(summary: Dict[str, Any]) -> ModuleSignal:
    direction = _direction_from_text(
        f"{summary.get('summary', '')}{summary.get('advice', '')}",
        ["吉", "可", "顺", "成", "有利", "推进"],
        ["凶", "阻", "慎", "缓", "难", "不利"],
    )
    moving_count = len(summary.get("dongyao", []) or [])
    certainty = max(45.0, 80.0 - moving_count * 8)
    return ModuleSignal(
        module="liuyao",
        layer="tactical",
        baseline_strength=55.0,
        timing_window=68.0,
        external_support=60.0,
        internal_resistance=40.0 if direction >= 0 else 58.0,
        risk_exposure=42.0 if direction >= 0 else 65.0,
        certainty=certainty,
        actionability=72.0,
        direction_score=direction,
        rationale=[
            summary.get("summary", ""),
            summary.get("advice", ""),
        ],
        raw=summary,
    )


def signal_from_meihua(summary: Dict[str, Any]) -> ModuleSignal:
    relation = summary.get("relation", "")
    relation_direction = {
        "用生体": 0.55,
        "体克用": 0.25,
        "比和": 0.35,
        "体生用": -0.15,
        "用克体": -0.55,
    }.get(relation, 0.0)
    return ModuleSignal(
        module="meihua",
        layer="tactical",
        baseline_strength=52.0,
        timing_window=64.0,
        external_support=57.0 if relation_direction >= 0 else 44.0,
        internal_resistance=46.0 if relation_direction >= 0 else 62.0,
        risk_exposure=40.0 if relation_direction >= 0 else 66.0,
        certainty=66.0,
        actionability=76.0,
        direction_score=relation_direction,
        rationale=[
            summary.get("summary", ""),
            summary.get("advice", ""),
            relation,
        ],
        raw=summary,
    )


def signal_from_qimen(summary: Dict[str, Any]) -> ModuleSignal:
    fortune = summary.get("matter_fortune", "") or ""
    direction = {
        "大吉": 0.8,
        "吉": 0.45,
        "中平": 0.0,
        "凶": -0.45,
        "大凶": -0.8,
    }.get(fortune, 0.0)
    return ModuleSignal(
        module="qimen",
        layer="window",
        baseline_strength=58.0,
        timing_window=82.0 if direction > 0 else 42.0,
        external_support=78.0 if summary.get("best_direction") else 52.0,
        internal_resistance=35.0 if direction > 0 else 68.0,
        risk_exposure=35.0 if direction > 0 else 72.0,
        certainty=72.0,
        actionability=80.0,
        direction_score=direction,
        rationale=[
            summary.get("matter_advice", ""),
            summary.get("best_direction", ""),
        ],
        raw=summary,
    )


def signal_from_zeri(summary: Dict[str, Any]) -> ModuleSignal:
    score = float(summary.get("score", 50) or 50)
    level = summary.get("level", "")
    direction = {
        "大吉": 0.75,
        "吉": 0.45,
        "平": 0.0,
        "凶": -0.45,
        "大凶": -0.75,
    }.get(level, 0.0)
    return ModuleSignal(
        module="zeri",
        layer="timing",
        baseline_strength=50.0,
        timing_window=score,
        external_support=55.0,
        internal_resistance=max(20.0, 90.0 - score),
        risk_exposure=max(15.0, 100.0 - score),
        certainty=min(88.0, 45.0 + score * 0.45),
        actionability=74.0,
        direction_score=direction,
        rationale=[
            summary.get("fortune_advice", ""),
            f"{summary.get('level', '')} {summary.get('score', 0)}分",
        ],
        raw=summary,
    )


def build_unified_world_model(
    question: str,
    profile: Dict[str, Any],
    module_summaries: Dict[str, Any],
    weight_overrides: Dict[str, Dict[str, float]] | None = None,
) -> Dict[str, Any]:
    decision_type = infer_decision_type(question, profile)
    signals: List[ModuleSignal] = []

    if module_summaries.get("bazi"):
        signals.append(signal_from_bazi(module_summaries["bazi"]))
    if module_summaries.get("ziwei"):
        signals.append(signal_from_ziwei(module_summaries["ziwei"]))
    if module_summaries.get("fengshui"):
        signals.append(signal_from_fengshui(module_summaries["fengshui"]))
    if module_summaries.get("liuyao"):
        signals.append(signal_from_liuyao(module_summaries["liuyao"]))
    if module_summaries.get("meihua"):
        signals.append(signal_from_meihua(module_summaries["meihua"]))
    if module_summaries.get("qimen"):
        signals.append(signal_from_qimen(module_summaries["qimen"]))
    if module_summaries.get("zeri"):
        signals.append(signal_from_zeri(module_summaries["zeri"]))

    environment = build_environment_modifiers(profile, question)
    adjusted_signals = apply_environment_modifiers(signals, environment)

    aggregate = {
        "baseline_strength": round(sum(signal.baseline_strength for signal in adjusted_signals) / len(adjusted_signals), 2) if adjusted_signals else 0.0,
        "timing_window": round(sum(signal.timing_window for signal in adjusted_signals) / len(adjusted_signals), 2) if adjusted_signals else 0.0,
        "external_support": round(sum(signal.external_support for signal in adjusted_signals) / len(adjusted_signals), 2) if adjusted_signals else 0.0,
        "internal_resistance": round(sum(signal.internal_resistance for signal in adjusted_signals) / len(adjusted_signals), 2) if adjusted_signals else 0.0,
        "risk_exposure": round(sum(signal.risk_exposure for signal in adjusted_signals) / len(adjusted_signals), 2) if adjusted_signals else 0.0,
        "certainty": round(sum(signal.certainty for signal in adjusted_signals) / len(adjusted_signals), 2) if adjusted_signals else 0.0,
        "actionability": round(sum(signal.actionability for signal in adjusted_signals) / len(adjusted_signals), 2) if adjusted_signals else 0.0,
        "direction_score": round(sum(signal.direction_score for signal in adjusted_signals) / len(adjusted_signals), 3) if adjusted_signals else 0.0,
    }

    vector = UnifiedEnergyVector(
        decision_type=decision_type,
        signals=adjusted_signals,
        aggregate=aggregate,
    )
    arbitration = arbitrate_signals(adjusted_signals, decision_type, weight_overrides=weight_overrides)
    return {
        "decision_type": decision_type,
        "environment": environment,
        "world_model": vector.to_dict(),
        "arbitration": arbitration,
    }
