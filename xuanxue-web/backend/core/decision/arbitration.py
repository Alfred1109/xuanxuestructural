"""
仲裁引擎
Rule-based arbitration engine for multi-module decision support.
"""

import math
from typing import Any, Dict, List

from .signal_schema import ModuleSignal
from .weight_tuning import DEFAULT_WEIGHT_PRESETS


def _normalize_weights(signals: List[ModuleSignal], decision_type: str, weight_overrides: Dict[str, Dict[str, float]] | None = None) -> Dict[str, float]:
    presets = weight_overrides or DEFAULT_WEIGHT_PRESETS
    preset = presets.get(decision_type, presets.get("balanced", DEFAULT_WEIGHT_PRESETS["balanced"]))
    weights = {signal.module: preset.get(signal.module, 0.05) for signal in signals}
    total = sum(weights.values()) or 1.0
    return {module: value / total for module, value in weights.items()}


def _label_entropy(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def arbitrate_signals(signals: List[ModuleSignal], decision_type: str, weight_overrides: Dict[str, Dict[str, float]] | None = None) -> Dict[str, Any]:
    if not signals:
        return {
            "weights": {},
            "weighted_scores": {},
            "consensus": [],
            "conflicts": [],
            "entropy": {
                "score": 100.0,
                "label": "high",
                "reason": "无可用模块信号，无法形成稳定决策。",
            },
            "recommendation": {
                "action_level": "wait",
                "decision_expectancy": 0.0,
                "risk_hedges": ["等待更多信息或补充完整输入。"],
            },
        }

    weights = _normalize_weights(signals, decision_type, weight_overrides=weight_overrides)
    weighted_scores = {
        "baseline_strength": 0.0,
        "timing_window": 0.0,
        "external_support": 0.0,
        "internal_resistance": 0.0,
        "risk_exposure": 0.0,
        "certainty": 0.0,
        "actionability": 0.0,
        "direction_score": 0.0,
    }
    directions: List[float] = []
    consensus: List[str] = []
    conflicts: List[str] = []

    for signal in signals:
        weight = weights[signal.module]
        directions.append(signal.direction_score)
        weighted_scores["baseline_strength"] += signal.baseline_strength * weight
        weighted_scores["timing_window"] += signal.timing_window * weight
        weighted_scores["external_support"] += signal.external_support * weight
        weighted_scores["internal_resistance"] += signal.internal_resistance * weight
        weighted_scores["risk_exposure"] += signal.risk_exposure * weight
        weighted_scores["certainty"] += signal.certainty * weight
        weighted_scores["actionability"] += signal.actionability * weight
        weighted_scores["direction_score"] += signal.direction_score * weight

        if signal.direction_score >= 0.2:
            consensus.append(f"{signal.module} 倾向支持行动")
        elif signal.direction_score <= -0.2:
            conflicts.append(f"{signal.module} 倾向提醒谨慎")

    mean_direction = sum(directions) / len(directions)
    variance = sum((value - mean_direction) ** 2 for value in directions) / len(directions)
    spread = (max(directions) - min(directions)) if len(directions) > 1 else 0.0
    entropy_score = max(0.0, min(100.0, math.sqrt(variance) * 100 + spread * 20))
    entropy_label = _label_entropy(entropy_score)

    baseline = weighted_scores["baseline_strength"]
    timing = weighted_scores["timing_window"]
    risk = weighted_scores["risk_exposure"]
    direction = weighted_scores["direction_score"]

    if entropy_score >= 70 or risk >= 70:
        action_level = "wait"
    elif baseline < 45 and timing < 55:
        action_level = "avoid"
    elif direction >= 0.35 and timing >= 60 and risk < 55:
        action_level = "proceed"
    else:
        action_level = "probe"

    expectancy = max(
        0.0,
        min(
            100.0,
            baseline * 0.25 + timing * 0.25 + weighted_scores["external_support"] * 0.2
            + weighted_scores["certainty"] * 0.15 + weighted_scores["actionability"] * 0.15
            - risk * 0.2 - weighted_scores["internal_resistance"] * 0.2
            + direction * 15,
        ),
    )

    hedges: List[str] = []
    if baseline < 50:
        hedges.append("命理承载力偏弱，建议先缩小动作规模。")
    if timing < 55:
        hedges.append("窗口期不够集中，优先等待更明确时机。")
    if risk >= 60:
        hedges.append("先准备风险兜底方案，不宜一次性重仓。")
    if entropy_score >= 40:
        hedges.append("多模块意见分歧较大，建议先小规模试探。")
    if not hedges:
        hedges.append("顺势推进即可，但仍需保留一档缓冲方案。")

    entropy_reason = (
        "模块结论高度分歧，信息噪声偏大。"
        if entropy_label == "high"
        else "模块存在一定分歧，适合试探性行动。"
        if entropy_label == "medium"
        else "模块判断相对一致，可形成较稳定建议。"
    )

    return {
        "weights": weights,
        "weighted_scores": weighted_scores,
        "consensus": consensus,
        "conflicts": conflicts,
        "entropy": {
            "score": round(entropy_score, 2),
            "label": entropy_label,
            "reason": entropy_reason,
        },
        "recommendation": {
            "action_level": action_level,
            "decision_expectancy": round(expectancy, 2),
            "risk_hedges": hedges,
        },
    }
