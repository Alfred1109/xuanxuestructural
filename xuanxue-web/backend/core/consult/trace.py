import json
from typing import Any, Dict, List, Optional

from ..decision.kernel import build_unified_world_model
from ..decision.weight_tuning import resolve_effective_weight_presets
from .models import TraceGraph, TraceStep
from .router import module_label


def _compact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _compact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_compact(item) for item in value]
    return value


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
        formulas: Optional[List[str]] = None,
        derivation: Optional[Dict[str, Any]] = None,
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
                formulas=[str(item) for item in (formulas or []) if str(item)],
                derivation=_compact(derivation or {}),
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
        " -> ".join(module_label(module) for module in modules) or "未命中专门模块",
        inputs={"matter_type": profile.get("matter_type"), "purpose": profile.get("purpose")},
        rule="按问题类型路由到八字、六爻、奇门、择日子系统",
        outputs={"modules": modules},
        evidence=[f"命中模块：{module_label(module)}" for module in modules],
        previous=last_step,
    )

    if "bazi" in modules and profile.get("birth"):
        bazi_result = module_results.get("bazi", {})
        bazi_analysis = bazi_result.get("analysis", {})
        bazi_advanced = bazi_result.get("advanced_analysis", {}).get("geju", {})
        bazi_trace = bazi_result.get("calc_trace", {})
        last_step = add_step(
            "bazi_year",
            "八字定年柱",
            "先判断是否过立春，再确定年份所属",
            inputs={
                "birth": profile.get("birth"),
                "gender": profile.get("gender"),
            },
            rule="以立春为八字年份分界点，立春前按上一年，立春后按当年",
            outputs={
                "year_pillar": bazi_result.get("bazi", {}).get("year"),
            },
            evidence=[
                f"年柱：{bazi_result.get('bazi', {}).get('year')}",
                bazi_trace.get("year_pillar", {}).get("comparison", ""),
            ],
            formulas=[bazi_trace.get("year_pillar", {}).get("formula", "")],
            derivation=bazi_trace.get("year_pillar", {}),
            previous=last_step,
        )
        last_step = add_step(
            "bazi_month",
            "八字定月柱",
            "按节气边界落月序，再映射月干月支",
            inputs={
                "birth": profile.get("birth"),
                "year_pillar": bazi_result.get("bazi", {}).get("year"),
            },
            rule="寅月起于立春，之后按惊蛰、清明等节气逐段推进月序",
            outputs={
                "month_pillar": bazi_result.get("bazi", {}).get("month"),
            },
            evidence=[
                f"月柱：{bazi_result.get('bazi', {}).get('month')}",
            ],
            formulas=[bazi_trace.get("month_pillar", {}).get("formula", "")],
            derivation=bazi_trace.get("month_pillar", {}),
            previous=last_step,
        )
        last_step = add_step(
            "bazi_day",
            "八字定日柱",
            "以基准日差推日柱",
            inputs={
                "birth": profile.get("birth"),
            },
            rule="以 1900-01-01 为基准日，按日差映射六十甲子索引",
            outputs={
                "day_pillar": bazi_result.get("bazi", {}).get("day"),
            },
            evidence=[
                f"日柱：{bazi_result.get('bazi', {}).get('day')}",
            ],
            formulas=[bazi_trace.get("day_pillar", {}).get("formula", "")],
            derivation=bazi_trace.get("day_pillar", {}),
            previous=last_step,
        )
        last_step = add_step(
            "bazi_hour",
            "八字定时柱",
            "先定时支，再按日干起时推时干",
            inputs={
                "day_pillar": bazi_result.get("bazi", {}).get("day"),
                "hour": profile.get("birth", {}).get("hour"),
            },
            rule="时支按 2 小时一段循环，时干按日干分组起算",
            outputs={
                "hour_pillar": bazi_result.get("bazi", {}).get("hour"),
            },
            evidence=[
                f"时柱：{bazi_result.get('bazi', {}).get('hour')}",
            ],
            formulas=[bazi_trace.get("hour_pillar", {}).get("formula", "")],
            derivation=bazi_trace.get("hour_pillar", {}),
            previous=last_step,
        )
        last_step = add_step(
            "bazi_wuxing",
            "八字计五行",
            "天干、地支、藏干按权重累加",
            inputs={
                "pillars": bazi_result.get("bazi", {}),
            },
            rule="天干权重=1，地支权重=1，地支藏干权重=0.5，最后按五行汇总",
            outputs={
                "wuxing_count": bazi_result.get("wuxing_count", {}),
            },
            evidence=[
                bazi_analysis.get("wuxing_summary", ""),
            ],
            formulas=[bazi_trace.get("wuxing_count", {}).get("formula", "")],
            derivation=bazi_trace.get("wuxing_count", {}),
            previous=last_step,
        )
        last_step = add_step(
            "bazi_shishen",
            "八字判十神",
            "以日干为我，逐一比较其他天干关系",
            inputs={
                "day_master": bazi_trace.get("shishen", {}).get("day_master", {}),
                "tiangan": bazi_result.get("tiangan", []),
            },
            rule="先判五行关系（同/我生/我克/生我/克我），再判阴阳同异映射十神",
            outputs={
                "shishen": bazi_result.get("shishen", {}),
            },
            evidence=[
                f"十神：{json.dumps(bazi_result.get('shishen', {}), ensure_ascii=False)}",
            ],
            formulas=[bazi_trace.get("shishen", {}).get("formula", "")],
            derivation=bazi_trace.get("shishen", {}),
            previous=last_step,
        )
        last_step = add_step(
            "bazi_dayun",
            "八字排大运",
            "先判顺逆与起运年龄，再从月柱推八步大运",
            inputs={
                "month_pillar": bazi_result.get("bazi", {}).get("month"),
                "gender": profile.get("gender"),
            },
            rule="男阳女阴顺排，男阴女阳逆排；起运年龄按出生与节令差值约 3 天 1 岁",
            outputs={
                "dayun": bazi_result.get("dayun", []),
            },
            evidence=[
                bazi_trace.get("dayun", {}).get("start_age_formula", ""),
            ],
            formulas=[bazi_trace.get("dayun", {}).get("start_age_formula", "")],
            derivation=bazi_trace.get("dayun", {}),
            previous=last_step,
        )
        last_step = add_step(
            "bazi_judge",
            "八字综合判读",
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
        liuyao_trace = liuyao_result.get("calc_trace", {})
        last_step = add_step(
            "liuyao_cast",
            "六爻起卦",
            "六次成爻值推导本卦、动爻与变卦",
            inputs={"question": question},
            rule="六次铜钱结果按自下而上定六爻，6/9 为动爻，变位后得到变卦",
            outputs={
                "bengua": liuyao_result.get("gua_info", {}).get("bengua", {}),
                "biangua": liuyao_result.get("gua_info", {}).get("biangua", {}),
                "dongyao": liuyao_result.get("gua_info", {}).get("dongyao", []),
            },
            evidence=[
                f"本卦：{liuyao_result.get('gua_info', {}).get('bengua', {}).get('name', '')}",
                f"变卦：{liuyao_result.get('gua_info', {}).get('biangua', {}).get('name', '')}",
            ],
            formulas=[liuyao_trace.get("cast", {}).get("formula", "")],
            derivation=liuyao_trace,
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

    if "meihua" in modules:
        meihua_result = module_results.get("meihua", {})
        interpretation = meihua_result.get("interpretation", {})
        meihua_trace = meihua_result.get("calc_trace", {})
        last_step = add_step(
            "meihua_cast",
            "梅花起卦",
            "按时间或数字求上卦、下卦与动爻",
            inputs={
                "question": question,
                "method": meihua_result.get("method", "time"),
            },
            rule="梅花易数先取数，再以 8 定卦、以 6 定动爻，形成本卦与变卦",
            outputs={
                "bengua": meihua_result.get("gua_info", {}).get("bengua", {}),
                "hugua": meihua_result.get("gua_info", {}).get("hugua", {}),
                "biangua": meihua_result.get("gua_info", {}).get("biangua", {}),
                "moving_line": meihua_result.get("gua_info", {}).get("moving_line", 0),
            },
            evidence=[
                f"本卦：{meihua_result.get('gua_info', {}).get('bengua', {}).get('name', '')}",
                f"互卦：{meihua_result.get('gua_info', {}).get('hugua', {}).get('name', '')}",
                f"变卦：{meihua_result.get('gua_info', {}).get('biangua', {}).get('name', '')}",
            ],
            formulas=meihua_trace.get("indexes", {}).get("formula", []),
            derivation=meihua_trace,
            previous=last_step,
        )
        last_step = add_step(
            "meihua_judge",
            "梅花判体用",
            "根据体用、生克、动爻判断事情趋势",
            inputs={
                "tiyong": meihua_result.get("gua_info", {}).get("tiyong", {}),
            },
            rule="以下卦为体、上卦为用，结合五行生克关系与动爻位置综合判断",
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
        qimen_trace = qimen_result.get("calc_trace", {})
        last_step = add_step(
            "qimen_dun",
            "奇门定阴阳遁与局数",
            "先比较冬至、夏至，再求局数",
            inputs={
                "time": qimen_result.get("时间信息", {}),
                "matter_type": profile.get("matter_type", "通用"),
            },
            rule="冬至到夏至为阳遁，夏至到冬至为阴遁；局数按月份和日期简化取模",
            outputs={
                "dun": qimen_result.get("遁甲信息", {}),
            },
            evidence=[
                f"阴阳遁：{qimen_result.get('遁甲信息', {}).get('阴阳遁', '')}",
                f"局数：{qimen_result.get('遁甲信息', {}).get('局数', '')}",
            ],
            formulas=[qimen_trace.get("dun_and_ju", {}).get("ju_formula", "")],
            derivation=qimen_trace.get("dun_and_ju", {}),
            previous=last_step,
        )
        last_step = add_step(
            "qimen_chart",
            "奇门布九宫",
            "按局数和值符偏移布地盘、天盘、门、星、神",
            inputs={
                "dun": qimen_result.get("遁甲信息", {}),
                "pillars": qimen_trace.get("pillars", {}),
            },
            rule="依九宫顺序落地盘，天盘按宫序+局数，门星神按宫序+值符偏移",
            outputs={
                "chart": qimen_result.get("九宫盘", {}),
            },
            evidence=[
                f"值符偏移：{qimen_trace.get('layout', {}).get('zhifu_offset', '')}",
            ],
            formulas=[qimen_trace.get("layout", {}).get("formula", "")],
            derivation=qimen_trace.get("layout", {}),
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
        zeri_trace = today_fortune.get("calc_trace", {})
        last_step = add_step(
            "zeri_jianxing",
            "择日定建星",
            "按月支、日支索引求建星",
            inputs={
                "date": today_fortune.get("date", ""),
                "purpose": profile.get("purpose", "通用"),
            },
            rule="建星从月建起顺数，以日支相对月支的偏移决定",
            outputs={
                "jianxing": today_fortune.get("jianxing", ""),
            },
            evidence=[
                f"建星：{today_fortune.get('jianxing', '')}",
            ],
            formulas=[zeri_trace.get("jianxing", {}).get("formula", "")],
            derivation=zeri_trace.get("jianxing", {}),
            previous=last_step,
        )
        last_step = add_step(
            "zeri_shier",
            "择日定十二神",
            "按日干定起点，再按日支推进",
            inputs={
                "day_ganzhi": zeri_trace.get("ganzhi", {}).get("day_ganzhi", ""),
            },
            rule="甲己起青龙，乙庚起天德，丙辛起司命，丁壬起朱雀，戊癸起玉堂",
            outputs={
                "shier_shen": today_fortune.get("shier_shen", ""),
                "huangdao_type": today_fortune.get("huangdao_type", ""),
            },
            evidence=[
                f"十二神：{today_fortune.get('shier_shen', '')}",
            ],
            formulas=[zeri_trace.get("shier_shen", {}).get("formula", "")],
            derivation=zeri_trace.get("shier_shen", {}),
            previous=last_step,
        )
        last_step = add_step(
            "zeri_score",
            "择日综合评分",
            "建星、黄黑道、星宿、宜忌合成总分",
            inputs={
                "date": today_fortune.get("date", ""),
                "purpose": profile.get("purpose", "通用"),
            },
            rule="基础分 50 起，再按建星级别和黄黑道加减分，映射最终吉凶等级",
            outputs={
                "level": today_fortune.get("level", ""),
                "score": today_fortune.get("score", 0),
                "suitable": today_fortune.get("suitable", []),
                "avoid": today_fortune.get("avoid", []),
            },
            evidence=[
                f"评分：{today_fortune.get('score', 0)}",
            ],
            derivation=zeri_trace.get("score", {}),
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
    effective_weights = resolve_effective_weight_presets()
    decision_kernel = build_unified_world_model(question, profile, module_summaries, weight_overrides=effective_weights)
    last_step = add_step(
        "environment",
        "环境修正",
        "把地点、用途、紧迫度、博弈语境映射为环境修正项",
        inputs={
            "question": question,
            "profile": profile,
        },
        rule="外部上下文不替代术数判断，只作为环境噪声与执行压力修正层",
        outputs=decision_kernel.get("environment", {}),
        evidence=[
            f"修正项：{len(decision_kernel.get('environment', {}).get('modifiers', []))}",
        ],
        previous=last_step,
    )
    last_step = add_step(
        "world_model",
        "统一世界模型",
        "把各术数摘要映射为统一决策信号",
        inputs={
            "question": question,
            "modules": list(module_summaries.keys()),
        },
        rule="不同术数先转成统一信号字段，再进入决策仲裁层",
        outputs=decision_kernel.get("world_model", {}),
        evidence=[
            f"决策类型：{decision_kernel.get('decision_type', '')}",
            f"信号数：{len(decision_kernel.get('world_model', {}).get('signals', []))}",
        ],
        previous=last_step,
    )
    last_step = add_step(
        "arbitration",
        "仲裁引擎",
        "按决策类型分配权重并处理模块冲突",
        inputs=decision_kernel.get("world_model", {}),
        rule="根据战略/战术/择时等类型动态分配模块权重，并计算决策熵值",
        outputs=decision_kernel.get("arbitration", {}),
        evidence=[
            f"熵值：{decision_kernel.get('arbitration', {}).get('entropy', {}).get('score', 0)}",
            f"行动等级：{decision_kernel.get('arbitration', {}).get('recommendation', {}).get('action_level', '')}",
        ],
        previous=last_step,
    )
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
            "decision_kernel": decision_kernel,
            "effective_weights": effective_weights,
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
