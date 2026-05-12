from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


ORIENTATION_GROUPS = {
    "north": {"label": "北向", "support": 58, "risk": 42, "direction": 0.1},
    "south": {"label": "南向", "support": 74, "risk": 28, "direction": 0.45},
    "east": {"label": "东向", "support": 68, "risk": 34, "direction": 0.28},
    "west": {"label": "西向", "support": 54, "risk": 46, "direction": -0.05},
    "southeast": {"label": "东南向", "support": 78, "risk": 26, "direction": 0.55},
    "southwest": {"label": "西南向", "support": 63, "risk": 38, "direction": 0.18},
    "northeast": {"label": "东北向", "support": 57, "risk": 41, "direction": 0.08},
    "northwest": {"label": "西北向", "support": 61, "risk": 36, "direction": 0.2},
    "unknown": {"label": "未知朝向", "support": 50, "risk": 50, "direction": 0.0},
}

SCENE_TEMPLATES = {
    "home": {
        "label": "住宅",
        "focus": "居住稳定、作息与家人关系",
        "good": "宜保持采光通风、动静分区清晰，减少尖角冲射。",
        "bad": "需注意杂物堆压、卧室受压和门窗气流紊乱。",
    },
    "office": {
        "label": "办公",
        "focus": "专注效率、资源流动与对外协作",
        "good": "宜保证主位稳定、背后有靠、视线开阔。",
        "bad": "需避免背后通道、座位受压和正冲门路。",
    },
    "shop": {
        "label": "经营场所",
        "focus": "客流、纳气与成交节奏",
        "good": "宜强化入口纳气、动线顺畅与收银位稳定。",
        "bad": "需避免入口受阻、收银位泄气和动线断裂。",
    },
    "generic": {
        "label": "通用空间",
        "focus": "空间稳定度与环境支持",
        "good": "宜保持明堂开阔、动线顺畅、采光均衡。",
        "bad": "需避免压迫、阴滞、冲煞和空间割裂。",
    },
}


def normalize_orientation(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    mapping = {
        "北": "north",
        "北向": "north",
        "north": "north",
        "南": "south",
        "南向": "south",
        "south": "south",
        "东": "east",
        "东向": "east",
        "east": "east",
        "西": "west",
        "西向": "west",
        "west": "west",
        "东南": "southeast",
        "东南向": "southeast",
        "southeast": "southeast",
        "西南": "southwest",
        "西南向": "southwest",
        "southwest": "southwest",
        "东北": "northeast",
        "东北向": "northeast",
        "northeast": "northeast",
        "西北": "northwest",
        "西北向": "northwest",
        "northwest": "northwest",
    }
    return mapping.get(text, "unknown")


def normalize_scene_type(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    mapping = {
        "住宅": "home",
        "家": "home",
        "home": "home",
        "办公": "office",
        "办公室": "office",
        "office": "office",
        "店铺": "shop",
        "商铺": "shop",
        "门店": "shop",
        "shop": "shop",
    }
    return mapping.get(text, "generic")


@dataclass
class FengShuiReading:
    question: str
    location: str
    orientation: str
    scene_type: str
    layout_note: str

    def to_dict(self) -> Dict[str, Any]:
        orientation_key = normalize_orientation(self.orientation)
        scene_key = normalize_scene_type(self.scene_type)
        orientation_info = ORIENTATION_GROUPS[orientation_key]
        scene_info = SCENE_TEMPLATES[scene_key]
        layout_risk = 48
        if any(term in self.layout_note for term in ["杂乱", "压梁", "冲门", "狭窄", "阴暗"]):
            layout_risk += 18
        if any(term in self.layout_note for term in ["通风", "采光", "开阔", "整洁", "有靠"]):
            layout_risk -= 14
        layout_risk = max(18, min(86, layout_risk))
        support_score = max(25, min(92, orientation_info["support"] - (layout_risk - 40) * 0.3))
        direction_score = max(-1.0, min(1.0, orientation_info["direction"] - (layout_risk - 45) / 120))

        recommended_direction = orientation_info["label"] if orientation_key != "unknown" else "宜优先选择东南、南或东方位"
        avoid_direction = "避免受冲、受压和门路直冲方位"
        summary = (
            f"{scene_info['label']}场景以{scene_info['focus']}为重点，"
            f"当前{orientation_info['label']}带来的基础支持度为{support_score:.0f}分，"
            f"空间风险约为{layout_risk}分。"
        )
        adjustment_advice = "；".join([
            scene_info["good"],
            scene_info["bad"],
            "若近期要推动关键事项，建议优先处理入口、主位和动线问题。",
        ])

        return {
            "question": self.question,
            "location": self.location,
            "scene_type": scene_info["label"],
            "orientation": orientation_info["label"],
            "layout_note": self.layout_note,
            "orientation_fit": round(support_score, 1),
            "layout_risk": layout_risk,
            "space_support": round(support_score, 1),
            "recommended_direction": recommended_direction,
            "avoid_direction": avoid_direction,
            "summary": summary,
            "adjustment_advice": adjustment_advice,
            "calc_trace": {
                "orientation": {
                    "formula": "朝向按方位组映射基础支持度与方向倾向",
                    "input": self.orientation,
                    "result": orientation_info,
                },
                "layout": {
                    "formula": "布局描述命中风险词与正向词后修正空间风险分",
                    "input": self.layout_note,
                    "result": {
                        "layout_risk": layout_risk,
                        "space_support": round(support_score, 1),
                    },
                },
                "summary": {
                    "formula": "综合朝向支持度、布局风险与场景模板生成空间建议",
                    "result": {
                        "recommended_direction": recommended_direction,
                        "avoid_direction": avoid_direction,
                    },
                },
            },
        }
