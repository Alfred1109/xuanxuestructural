from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from iztro_py.astro import by_solar_hour


def _extract_palace(palaces: List[Dict[str, Any]], palace_name: str) -> Dict[str, Any]:
    return next((palace for palace in palaces if palace.get("name") == palace_name), {})


def _flatten_stars(palaces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    stars: List[Dict[str, Any]] = []
    for palace in palaces:
        for star in palace.get("majorStars", []):
            stars.append(
                {
                    "palace": palace.get("name", ""),
                    "name": star.get("name", ""),
                    "brightness": star.get("brightness"),
                    "mutagen": star.get("mutagen"),
                    "scope": star.get("scope"),
                    "type": star.get("type"),
                }
            )
    return stars


def _extract_mutagens(stars: List[Dict[str, Any]]) -> Dict[str, str]:
    mapping = {"禄": "化禄", "权": "化权", "科": "化科", "忌": "化忌"}
    result = {label: "" for label in mapping.values()}
    for star in stars:
        mutagen = star.get("mutagen")
        if mutagen in mapping and not result[mapping[mutagen]]:
            result[mapping[mutagen]] = star.get("name", "")
    return result


def _major_star_names(palace: Dict[str, Any]) -> List[str]:
    return [item.get("name", "") for item in palace.get("majorStars", []) if item.get("name")]


def _infer_vectors(palaces: List[Dict[str, Any]]) -> Dict[str, str]:
    career = _extract_palace(palaces, "官禄宫")
    spouse = _extract_palace(palaces, "夫妻宫")
    health = _extract_palace(palaces, "疾厄宫")
    return {
        "career": "、".join(_major_star_names(career)) or "待结合官禄宫与大限细判",
        "relationship": "、".join(_major_star_names(spouse)) or "待结合夫妻宫与四化细判",
        "health": "、".join(_major_star_names(health)) or "待结合疾厄宫与福德宫细判",
    }


def _career_tone(stars: List[str]) -> str:
    if any(star in stars for star in ["武曲", "紫微", "天府"]):
        return "事业结构偏稳，适合承担资源、管理或长期经营型事务。"
    if any(star in stars for star in ["破军", "七杀", "贪狼"]):
        return "事业路径带突破与变化色彩，适合在变化中找机会。"
    if any(star in stars for star in ["太阳", "天梁", "天机"]):
        return "事业更重专业判断、规划能力与公共表达。"
    return "事业判断仍需结合官禄宫与大限进一步细判。"


def _relationship_tone(stars: List[str]) -> str:
    if any(star in stars for star in ["天相", "太阴", "天同"]):
        return "关系模式偏重陪伴、协调与情绪互信。"
    if any(star in stars for star in ["巨门", "廉贞", "破军"]):
        return "关系领域容易出现拉扯、强互动或价值观磨合。"
    return "关系模式需结合夫妻宫、福德宫与四化继续细判。"


def _wealth_tone(stars: List[str]) -> str:
    if any(star in stars for star in ["武曲", "太阴", "天府"]):
        return "财务结构偏向稳健积累，适合重视现金流与资产沉淀。"
    if any(star in stars for star in ["贪狼", "破军", "七杀"]):
        return "财务机会和波动并存，更适合动态把握机会。"
    return "财务判断宜结合财帛宫与运限节奏进一步确认。"


def _health_tone(stars: List[str]) -> str:
    if any(star in stars for star in ["天梁", "天府", "太阴"]):
        return "健康宫结构偏守成，重在长期调养与节律稳定。"
    if any(star in stars for star in ["巨门", "廉贞", "破军"]):
        return "健康宫提示要注意作息、情绪与消耗型问题。"
    return "健康判断仍需结合疾厄宫、福德宫与流年状态细判。"


def _mutagen_lines(four_transformations: Dict[str, str]) -> List[str]:
    return [
        f"{label}：{star}" for label, star in four_transformations.items() if star
    ]


@dataclass
class ZiWeiChart:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    gender: str

    def to_dict(self) -> Dict[str, Any]:
        astrolabe = by_solar_hour(
            f"{self.year:04d}-{self.month:02d}-{self.day:02d}",
            self.hour,
            self.gender,
            language="zh-CN",
        )
        data = astrolabe.to_iztro_dict()
        palaces = data.get("palaces", [])
        soul_ref = astrolabe.get_soul_palace()
        body_ref = astrolabe.get_body_palace()
        soul_palace_name = getattr(soul_ref, "name", "")
        body_palace_name = getattr(body_ref, "name", "")
        soul_palace = _extract_palace(palaces, soul_palace_name)
        body_palace = _extract_palace(palaces, body_palace_name)
        all_major_stars = _flatten_stars(palaces)
        vectors = _infer_vectors(palaces)
        four_transformations = _extract_mutagens(all_major_stars)
        career_palace = _extract_palace(palaces, "官禄宫")
        wealth_palace = _extract_palace(palaces, "财帛宫")
        spouse_palace = _extract_palace(palaces, "夫妻宫")
        health_palace = _extract_palace(palaces, "疾厄宫")

        return {
            "profile": {
                "year": self.year,
                "month": self.month,
                "day": self.day,
                "hour": self.hour,
                "minute": self.minute,
                "gender": self.gender,
            },
            "solar_date": data.get("solarDate", ""),
            "lunar_date": data.get("lunarDate", ""),
            "chinese_date": data.get("chineseDate", ""),
            "time": data.get("time", ""),
            "time_range": data.get("timeRange", ""),
            "sign": data.get("sign", ""),
            "zodiac": data.get("zodiac", ""),
            "five_elements_class": data.get("fiveElementsClass", ""),
            "minggong": {
                "name": soul_palace.get("name", ""),
                "earthly_branch": data.get("earthlyBranchOfSoulPalace", ""),
                "major_stars": soul_palace.get("majorStars", []),
            },
            "shengong": {
                "name": body_palace.get("name", ""),
                "earthly_branch": data.get("earthlyBranchOfBodyPalace", ""),
                "major_stars": body_palace.get("majorStars", []),
            },
            "major_stars": all_major_stars,
            "four_transformations": four_transformations,
            "fortune_cycle": {
                "ranges": [
                    {
                        "palace": palace.get("name", ""),
                        "range": list((palace.get("decadal") or {}).get("range", [])),
                    }
                    for palace in palaces
                    if palace.get("decadal")
                ],
            },
            "core_palaces": {
                "minggong": soul_palace,
                "shengong": body_palace,
                "career": career_palace,
                "wealth": wealth_palace,
                "relationship": spouse_palace,
                "health": health_palace,
            },
            "palaces": palaces,
            "palace_snapshot": [
                {
                    "name": palace.get("name", ""),
                    "earthly_branch": palace.get("earthlyBranch", ""),
                    "major_stars": [item.get("name", "") for item in palace.get("majorStars", [])],
                    "is_original_palace": palace.get("isOriginalPalace", False),
                    "is_body_palace": palace.get("isBodyPalace", False),
                }
                for palace in palaces
            ],
            "vectors": vectors,
            "calc_trace": {
                "source": "iztro-py by_solar_hour",
                "solar_input": data.get("solarDate", ""),
                "lunar_output": data.get("lunarDate", ""),
                "chinese_date": data.get("chineseDate", ""),
                "minggong": {
                    "formula": "依据农历月数与时辰按紫微斗数命宫规则定位（由 iztro-py 实现）",
                    "result": soul_palace.get("name", ""),
                    "earthly_branch": data.get("earthlyBranchOfSoulPalace", ""),
                },
                "shengong": {
                    "formula": "依据出生时辰与命盘结构按紫微斗数身宫规则定位（由 iztro-py 实现）",
                    "result": body_palace.get("name", ""),
                    "earthly_branch": data.get("earthlyBranchOfBodyPalace", ""),
                },
                "four_transformations": {
                    "formula": "依据年干四化规则安置化禄、化权、化科、化忌（由 iztro-py 实现）",
                    "result": four_transformations,
                },
            },
        }


def analyze_ziwei_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    minggong = chart.get("minggong", {})
    shengong = chart.get("shengong", {})
    vectors = chart.get("vectors", {})
    core_palaces = chart.get("core_palaces", {})
    fortune_cycle = chart.get("fortune_cycle", {}).get("ranges", [])
    current_decadal = fortune_cycle[0] if fortune_cycle else {}
    ming_stars = _major_star_names(minggong)
    career_stars = _major_star_names(core_palaces.get("career", {}))
    relationship_stars = _major_star_names(core_palaces.get("relationship", {}))
    wealth_stars = _major_star_names(core_palaces.get("wealth", {}))
    health_stars = _major_star_names(core_palaces.get("health", {}))
    mutagen_lines = _mutagen_lines(chart.get("four_transformations", {}))
    summary = (
        f"命宫落在{minggong.get('name', '未知')}，身宫落在{shengong.get('name', '未知')}，"
        f"命宫主星以{'、'.join(ming_stars) or '待细判'}为核心。"
    )
    return {
        "summary": summary,
        "career_vector": _career_tone(career_stars),
        "relationship_vector": _relationship_tone(relationship_stars),
        "wealth_vector": _wealth_tone(wealth_stars),
        "health_vector": _health_tone(health_stars),
        "minggong_focus": "、".join(ming_stars) or vectors.get("career", ""),
        "mutagen_summary": "；".join(mutagen_lines) if mutagen_lines else "本盘四化需结合流年继续细判。",
        "current_decadal": current_decadal,
        "advice": "紫微斗数适合用于长期结构判断，正式决策建议结合八字底盘、当前问事模块与当前大限、流年窗口交叉验证。",
    }
