from typing import List, Optional


MODULE_LABELS = {
    "bazi": "八字",
    "liuyao": "六爻",
    "meihua": "梅花",
    "qimen": "奇门",
    "zeri": "择日",
}


def module_label(module_name: str) -> str:
    return MODULE_LABELS.get(module_name, module_name)


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
        "面试", "复合", "辞职", "升职", "转岗", "项目", "这件事",
    ]
    meihua_terms = [
        "数字", "号码", "时间起卦", "心念", "刚刚", "突然", "灵感", "征兆", "象", "预感",
    ]
    qimen_terms = [
        "方向", "方位", "怎么走", "布局", "策略", "局势", "当前", "现在", "近期",
        "怎么做", "如何做", "选择", "出路", "转机",
    ]
    zeri_terms = [
        "择日", "吉日", "哪天", "日期", "时间", "开业", "结婚", "搬家", "入宅",
        "签约", "出行", "动土", "安排",
    ]

    if any(term.lower() in text for term in liuyao_terms) or matter_type in ("婚姻", "求职", "求财", "学业", "诉讼", "疾病"):
        modules.append("liuyao")

    if any(term.lower() in text for term in meihua_terms) or ("liuyao" in modules and not has_birth):
        modules.append("meihua")

    if any(term.lower() in text for term in qimen_terms) or matter_type in ("求财", "求职", "出行", "婚姻"):
        modules.append("qimen")

    if any(term.lower() in text for term in zeri_terms) or purpose != "通用":
        modules.append("zeri")

    if not modules:
        modules = ["liuyao", "meihua", "qimen"]
        if has_birth:
            modules.insert(0, "bazi")

    seen = set()
    ordered: List[str] = []
    for module in modules:
        if module not in seen:
            ordered.append(module)
            seen.add(module)
    return ordered
