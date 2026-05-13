import json
from datetime import datetime
from typing import Any, Dict

from ..bazi_advanced import get_advanced_analysis
from ..bazi_core import BaZiChart
from ..decision_log import append_decision_log
from ..decision.kernel import build_unified_world_model
from ..decision.kernel import build_visual_rule_scores
from ..fengshui import FengShuiReading
from ..decision.weight_tuning import resolve_effective_weight_presets
from ..liuyao import divine
from ..llm_helper import llm_helper
from ..meihua import divine_meihua
from ..qimen import divine_qimen
from ..ziwei import ZiWeiChart, analyze_ziwei_chart
from ..zeri import find_auspicious_days, get_today_fortune
from .models import UnifiedConsultRequest
from .router import infer_consult_modules, normalize_matter_type, normalize_purpose
from .summarizers import (
    generate_simple_analysis,
    summarize_bazi_result,
    summarize_fengshui_result,
    summarize_liuyao_result,
    summarize_meihua_result,
    summarize_qimen_result,
    summarize_visual_result,
    summarize_ziwei_result,
    summarize_zeri_result,
)
from .trace import build_trace_graph


def has_complete_birth_payload(payload: UnifiedConsultRequest) -> bool:
    return all(
        value is not None
        for value in (payload.year, payload.month, payload.day, payload.hour, payload.gender)
    )


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
    fengshui = module_summaries.get("fengshui")
    if fengshui:
        lines.append(f"风水提示：{fengshui.get('summary', '')} 建议优先处理 {fengshui.get('recommended_direction', '')} 与空间动线。")
    visual = module_summaries.get("visual")
    if visual:
        if visual.get("mode") == "space":
            lines.append(f"现场观察：{visual.get('summary', '')} 该图片观察结果已并入空间层判断。")
        else:
            lines.append(f"微观参考：{visual.get('summary', '')} 仅作传统文化参考，不替代主命理结论。")
    zeri = module_summaries.get("zeri")
    if zeri:
        lines.append(f"择日提示：{zeri.get('level', '')}，评分 {zeri.get('score', 0)}，{zeri.get('fortune_advice', '')}")
    lines.append("总体建议：先顺着最稳定、阻力最小的路径推进，重要动作尽量与吉时、吉方和命盘优势保持一致。")
    return "\n".join(lines)


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
            "visual_context": payload.visual_context.model_dump() if payload.visual_context else None,
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

        if "ziwei" in modules and has_birth:
            ziwei_chart = ZiWeiChart(
                payload.year,
                payload.month,
                payload.day,
                payload.hour,
                payload.minute or 0,
                payload.gender or "男",
            )
            ziwei_result = ziwei_chart.to_dict()
            ziwei_result["analysis"] = analyze_ziwei_chart(ziwei_result)
            module_results["ziwei"] = ziwei_result
            module_summaries["ziwei"] = summarize_ziwei_result(ziwei_result)

        if "fengshui" in modules:
            fengshui_result = FengShuiReading(
                question=question,
                location=payload.location or "",
                orientation="",
                scene_type="office" if any(term in question for term in ["办公室", "工位", "办公"]) else "home" if any(term in question for term in ["住宅", "搬家", "入宅", "家里"]) else "generic",
                layout_note=question,
            ).to_dict()
            module_results["fengshui"] = fengshui_result
            module_summaries["fengshui"] = summarize_fengshui_result(fengshui_result)

        if payload.visual_context:
            visual_context = payload.visual_context.model_dump()
            if visual_context.get("mode") == "bundle":
                items = []
                for item in visual_context.get("items", []) or []:
                    item_rule_scores = item.get("rule_scores", {}) or build_visual_rule_scores({
                        "mode": item.get("mode"),
                        "structure": item.get("structure", {}),
                    })
                    items.append({
                        "mode": item.get("mode"),
                        "mode_label": {
                            "space": "空间 / 风水观察",
                            "palm": "手相参考",
                            "face": "面相参考",
                        }.get(item.get("mode"), "视觉观察"),
                        "question": item.get("question", ""),
                        "location": item.get("location", ""),
                        "scene_type": item.get("scene_type", ""),
                        "image_name": item.get("image_name", ""),
                        "analysis": item.get("analysis", ""),
                        "structure": item.get("structure", {}),
                        "rule_scores": item_rule_scores,
                    })
                visual_result = {
                    "mode": "bundle",
                    "mode_label": "多维视觉观察",
                    "question": visual_context.get("question", ""),
                    "location": visual_context.get("location", ""),
                    "scene_type": visual_context.get("scene_type", ""),
                    "image_name": visual_context.get("image_name", ""),
                    "analysis": visual_context.get("analysis", ""),
                    "disclaimer": visual_context.get("disclaimer", ""),
                    "items": items,
                    "calc_trace": {
                        "structure": {
                            "formula": "对三类图片分别做结构化提取，抽取可见空间/掌纹/面部特征，再汇总入统一问事。",
                            "input": {
                                "count": len(items),
                                "modes": [item.get("mode", "") for item in items],
                            },
                            "result": {item.get("mode", ""): item.get("structure", {}) for item in items},
                        },
                        "rule_scores": {
                            "formula": "将每类图片的结构提取结果映射成对应规则分表，再供统一决策核吸收。",
                            "input": {item.get("mode", ""): item.get("structure", {}) for item in items},
                            "result": {item.get("mode", ""): item.get("rule_scores", {}) for item in items},
                        },
                        "image": {
                            "formula": "图片观察结果由多模态模型基于可见特征生成，作为统一问事的补充输入。",
                            "input": {
                                "modes": [item.get("mode", "") for item in items],
                                "image_names": [item.get("image_name", "") for item in items],
                            },
                            "result": {
                                "summary": visual_context.get("analysis", "")[:240],
                            },
                        }
                    },
                }
            else:
                visual_result = {
                    "mode": visual_context.get("mode"),
                    "mode_label": {
                        "space": "空间 / 风水观察",
                        "palm": "手相参考",
                        "face": "面相参考",
                    }.get(visual_context.get("mode"), "视觉观察"),
                    "question": visual_context.get("question", ""),
                    "location": visual_context.get("location", ""),
                    "scene_type": visual_context.get("scene_type", ""),
                    "image_name": visual_context.get("image_name", ""),
                    "analysis": visual_context.get("analysis", ""),
                    "disclaimer": visual_context.get("disclaimer", ""),
                    "structure": visual_context.get("structure", {}),
                    "rule_scores": visual_context.get("rule_scores", {}) or build_visual_rule_scores({
                        "mode": visual_context.get("mode"),
                        "structure": visual_context.get("structure", {}),
                    }),
                    "calc_trace": {
                        "structure": {
                            "formula": "先对图片做结构化提取，抽取可见空间/掌纹/面部特征，再供统一问事吸收。",
                            "input": {
                                "mode": visual_context.get("mode", ""),
                                "image_name": visual_context.get("image_name", ""),
                            },
                            "result": visual_context.get("structure", {}),
                        },
                        "rule_scores": {
                            "formula": "将结构提取结果映射为空间支持度、风险暴露或参考可信度等规则分表。",
                            "input": visual_context.get("structure", {}),
                            "result": visual_context.get("rule_scores", {}) or build_visual_rule_scores({
                                "mode": visual_context.get("mode"),
                                "structure": visual_context.get("structure", {}),
                            }),
                        },
                        "image": {
                            "formula": "图片观察结果由多模态模型基于可见特征生成，作为统一问事的补充输入。",
                            "input": {
                                "mode": visual_context.get("mode", ""),
                                "image_name": visual_context.get("image_name", ""),
                                "location": visual_context.get("location", ""),
                                "scene_type": visual_context.get("scene_type", ""),
                            },
                            "result": {
                                "summary": visual_context.get("analysis", "")[:200],
                            },
                        }
                    },
                }
            module_results["visual"] = visual_result
            module_summaries["visual"] = summarize_visual_result(visual_result)
            if "visual" not in modules:
                modules.append("visual")

        if "liuyao" in modules:
            liuyao_result = divine(question)
            if llm_helper.is_available():
                ai_interpretation = llm_helper.enhance_liuyao_interpretation(liuyao_result)
                if ai_interpretation:
                    liuyao_result["ai_interpretation"] = ai_interpretation
            module_results["liuyao"] = liuyao_result
            module_summaries["liuyao"] = summarize_liuyao_result(liuyao_result)

        if "meihua" in modules:
            meihua_result = divine_meihua(question=question, method="time")
            module_results["meihua"] = meihua_result
            module_summaries["meihua"] = summarize_meihua_result(meihua_result)

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
        effective_weights = resolve_effective_weight_presets()
        decision_kernel = build_unified_world_model(question, profile, module_summaries, weight_overrides=effective_weights)
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
        decision_log = append_decision_log(
            {
                "question": question,
                "profile": profile,
                "intent": {
                    "modules": modules,
                    "matter_type": matter_type,
                    "purpose": purpose,
                },
                "module_summaries": module_summaries,
                "decision_kernel": decision_kernel,
                "effective_weights": effective_weights,
                "answer": answer,
            }
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
            "decision_kernel": decision_kernel,
            "effective_weights": effective_weights,
            "decision_log": decision_log,
            "answer": answer,
            "trace": trace.to_dict(),
            "ai": {
                "enabled": ai_enabled,
                "synthesized": synthesis is not None,
                "fallback": synthesis is None,
            },
        }


consultation_engine = ConsultationEngine()
