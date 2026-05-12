from typing import Any, Dict

from ..bazi_core import BaZiChart


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


def summarize_ziwei_result(result: Dict[str, Any]) -> Dict[str, Any]:
    analysis = result.get("analysis", {})
    return {
        "summary": analysis.get("summary", ""),
        "minggong": result.get("minggong", {}).get("name", ""),
        "shengong": result.get("shengong", {}).get("name", ""),
        "major_stars": [item.get("name", "") for item in result.get("major_stars", [])],
        "career_vector": analysis.get("career_vector", ""),
        "relationship_vector": analysis.get("relationship_vector", ""),
        "wealth_vector": analysis.get("wealth_vector", ""),
        "health_vector": analysis.get("health_vector", ""),
        "minggong_focus": analysis.get("minggong_focus", ""),
        "mutagen_summary": analysis.get("mutagen_summary", ""),
        "current_decadal": analysis.get("current_decadal", {}),
        "fortune_cycle": result.get("fortune_cycle", {}),
        "advice": analysis.get("advice", ""),
    }


def summarize_fengshui_result(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "summary": result.get("summary", ""),
        "location": result.get("location", ""),
        "scene_type": result.get("scene_type", ""),
        "orientation": result.get("orientation", ""),
        "orientation_fit": result.get("orientation_fit", 0),
        "layout_risk": result.get("layout_risk", 0),
        "space_support": result.get("space_support", 0),
        "recommended_direction": result.get("recommended_direction", ""),
        "avoid_direction": result.get("avoid_direction", ""),
        "adjustment_advice": result.get("adjustment_advice", ""),
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


def summarize_meihua_result(result: Dict[str, Any]) -> Dict[str, Any]:
    gua_info = result.get("gua_info", {})
    interpretation = result.get("interpretation", {})
    tiyong = gua_info.get("tiyong", {})
    return {
        "question": result.get("question", ""),
        "method": result.get("method", ""),
        "bengua": gua_info.get("bengua", {}).get("name", ""),
        "hugua": gua_info.get("hugua", {}).get("name", ""),
        "biangua": gua_info.get("biangua", {}).get("name", ""),
        "moving_line": gua_info.get("moving_line", 0),
        "relation": tiyong.get("relation", ""),
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


def generate_simple_analysis(chart: BaZiChart) -> dict:
    """生成简单的命理分析"""
    wuxing_count = chart.get_wuxing_count()

    max_wuxing = max(wuxing_count, key=wuxing_count.get)
    min_wuxing = min(wuxing_count, key=wuxing_count.get)

    wuxing_advice = {
        "木": {
            "strong": "木旺，性格直爽，适合从事创造性工作。注意肝胆健康。",
            "weak": "木弱，需要补木。适合多接触绿色，从事文化教育行业。",
        },
        "火": {
            "strong": "火旺，热情积极，适合从事社交、表演类工作。注意心血管健康。",
            "weak": "火弱，需要补火。适合多接触红色，从事热情洋溢的行业。",
        },
        "土": {
            "strong": "土旺，稳重踏实，适合从事管理、房地产工作。注意脾胃健康。",
            "weak": "土弱，需要补土。适合多接触黄色，从事稳定的行业。",
        },
        "金": {
            "strong": "金旺，果断坚毅，适合从事金融、技术工作。注意呼吸系统健康。",
            "weak": "金弱，需要补金。适合多接触白色，从事精密技术行业。",
        },
        "水": {
            "strong": "水旺，聪明灵活，适合从事智慧、流动性工作。注意肾脏健康。",
            "weak": "水弱，需要补水。适合多接触黑色，从事智慧型行业。",
        },
    }

    return {
        "wuxing_summary": f"五行中{max_wuxing}最旺（{wuxing_count[max_wuxing]:.1f}），{min_wuxing}最弱（{wuxing_count[min_wuxing]:.1f}）",
        "strong_element": {
            "element": max_wuxing,
            "count": wuxing_count[max_wuxing],
            "advice": wuxing_advice[max_wuxing]["strong"],
        },
        "weak_element": {
            "element": min_wuxing,
            "count": wuxing_count[min_wuxing],
            "advice": wuxing_advice[min_wuxing]["weak"],
        },
        "balance_advice": get_balance_advice(wuxing_count),
        "disclaimer": "以上分析仅供参考，具体情况需要结合完整命盘综合判断。",
    }


def get_balance_advice(wuxing_count: dict) -> str:
    """根据五行平衡给出建议"""
    max_count = max(wuxing_count.values())
    min_count = min(wuxing_count.values())
    diff = max_count - min_count

    if diff < 2:
        return "五行较为平衡，命局稳定，发展较为顺利。"
    if diff < 4:
        return "五行有一定偏颇，建议在生活中注意平衡，补足弱项。"
    return "五行偏颇较大，建议通过方位、颜色、职业等方式调整平衡。"
