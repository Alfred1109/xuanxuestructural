"""
环境修正层
Applies auditable real-world context modifiers onto decision signals.
"""

from typing import Any, Dict, List

from .signal_schema import ModuleSignal


def build_environment_modifiers(profile: Dict[str, Any], question: str) -> Dict[str, Any]:
    text = question or ""
    modifiers: List[Dict[str, Any]] = []

    if profile.get("location"):
        modifiers.append({
            "name": "location_context",
            "effect": {"external_support": 2.0, "certainty": 1.5},
            "reason": f"已提供地点信息：{profile.get('location')}",
        })

    visual_context = profile.get("visual_context") or {}
    if visual_context:
        mode = visual_context.get("mode", "")
        if mode == "bundle":
            item_modes = {item.get("mode", "") for item in (visual_context.get("items", []) or [])}
            if "space" in item_modes:
                modifiers.append({
                    "name": "visual_space_context",
                    "effect": {"external_support": 3.0, "certainty": 2.0, "actionability": 4.0},
                    "reason": "已提供空间照片观察结果，环境判断更贴近现场细节。",
                })
            if "palm" in item_modes or "face" in item_modes:
                modifiers.append({
                    "name": "visual_micro_reference",
                    "effect": {"certainty": 1.0, "actionability": 1.0},
                    "reason": "已提供微观图像参考，可作为文化层面的补充观察。",
                })
        elif mode == "space":
            modifiers.append({
                "name": "visual_space_context",
                "effect": {"external_support": 3.0, "certainty": 2.0, "actionability": 4.0},
                "reason": "已提供空间照片观察结果，环境判断更贴近现场细节。",
            })
        elif mode in ("palm", "face"):
            modifiers.append({
                "name": "visual_micro_reference",
                "effect": {"certainty": 1.0, "actionability": 1.0},
                "reason": "已提供微观图像参考，可作为文化层面的补充观察。",
            })

    if any(term in text for term in ["谈判", "合作", "签约", "客户", "对手"]):
        modifiers.append({
            "name": "game_context",
            "effect": {"risk_exposure": 4.0, "actionability": 3.0},
            "reason": "问题包含明显博弈语境，需要放大执行与风险维度。",
        })

    if any(term in text for term in ["马上", "今天", "立刻", "现在", "本周"]):
        modifiers.append({
            "name": "urgency_context",
            "effect": {"timing_window": 5.0, "certainty": -3.0},
            "reason": "问题具有即时性，窗口价值提升，但信息稳定性下降。",
        })

    if profile.get("purpose") not in (None, "", "通用"):
        modifiers.append({
            "name": "purpose_specificity",
            "effect": {"certainty": 4.0, "actionability": 4.0},
            "reason": f"用途明确为 {profile.get('purpose')}，判断边界更清晰。",
        })

    aggregate_effect = {
        "baseline_strength": 0.0,
        "timing_window": 0.0,
        "external_support": 0.0,
        "internal_resistance": 0.0,
        "risk_exposure": 0.0,
        "certainty": 0.0,
        "actionability": 0.0,
        "direction_score": 0.0,
    }
    for modifier in modifiers:
        for key, delta in modifier["effect"].items():
            aggregate_effect[key] += delta

    return {
        "modifiers": modifiers,
        "aggregate_effect": aggregate_effect,
    }


def apply_environment_modifiers(signals: List[ModuleSignal], environment: Dict[str, Any]) -> List[ModuleSignal]:
    effect = environment.get("aggregate_effect", {})
    adjusted: List[ModuleSignal] = []
    for signal in signals:
        updated = ModuleSignal(
            module=signal.module,
            layer=signal.layer,
            baseline_strength=max(0.0, min(100.0, signal.baseline_strength + effect.get("baseline_strength", 0.0))),
            timing_window=max(0.0, min(100.0, signal.timing_window + effect.get("timing_window", 0.0))),
            external_support=max(0.0, min(100.0, signal.external_support + effect.get("external_support", 0.0))),
            internal_resistance=max(0.0, min(100.0, signal.internal_resistance + effect.get("internal_resistance", 0.0))),
            risk_exposure=max(0.0, min(100.0, signal.risk_exposure + effect.get("risk_exposure", 0.0))),
            certainty=max(0.0, min(100.0, signal.certainty + effect.get("certainty", 0.0))),
            actionability=max(0.0, min(100.0, signal.actionability + effect.get("actionability", 0.0))),
            direction_score=max(-1.0, min(1.0, signal.direction_score + effect.get("direction_score", 0.0))),
            rationale=signal.rationale + [modifier["reason"] for modifier in environment.get("modifiers", [])],
            raw=signal.raw,
        )
        adjusted.append(updated)
    return adjusted
