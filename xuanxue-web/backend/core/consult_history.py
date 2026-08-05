"""
账号问事历史
Per-user consultation history stored in JSONL.
"""

from datetime import datetime, timezone
from collections import Counter
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .runtime.store import append_jsonl, iter_jsonl_reverse, read_jsonl, resolve_runtime_path


def _history_path():
    return resolve_runtime_path("CONSULT_HISTORY_PATH", "consult_history.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _build_brief_answer(answer: str) -> str:
    text = (answer or "").strip()
    if not text:
        return "已生成综合结论，请查看详情。"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        normalized = line.lstrip("#*-0123456789. ").strip()
        if not normalized:
            continue
        if len(normalized) <= 80:
            return normalized
        return normalized[:80].rstrip("，,;；:： ") + "…"
    return "已生成综合结论，请查看详情。"


def append_consult_history(user_id: str, consultation: Dict[str, Any]) -> Dict[str, Any]:
    history_id = str(uuid4())
    intent = consultation.get("intent") if isinstance(consultation.get("intent"), dict) else {}
    payload = {
        "history_id": history_id,
        "user_id": user_id,
        "created_at": _now_iso(),
        "question": consultation.get("question") or "",
        "brief_answer": _build_brief_answer(str(consultation.get("answer") or "")),
        "answer": consultation.get("answer") or "",
        "intent": {
            "modules": intent.get("modules") or [],
            "matter_type": intent.get("matter_type") or "通用",
            "purpose": intent.get("purpose") or "通用",
        },
        "profile": consultation.get("profile") or {},
        "module_summaries": consultation.get("module_summaries") or {},
        "ai": consultation.get("ai") or {},
        "workspace": consultation,
    }
    append_jsonl(_history_path(), payload)
    return {
        "saved": True,
        "history_id": history_id,
    }


def _history_list_item(entry: Dict[str, Any]) -> Dict[str, Any]:
    intent = entry.get("intent") if isinstance(entry.get("intent"), dict) else {}
    return {
        "history_id": entry.get("history_id"),
        "created_at": entry.get("created_at"),
        "question": entry.get("question") or "",
        "brief_answer": entry.get("brief_answer") or "",
        "modules": intent.get("modules") or [],
        "matter_type": intent.get("matter_type") or "通用",
        "purpose": intent.get("purpose") or "通用",
    }


def list_consult_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for item in iter_jsonl_reverse(_history_path()):
        if item.get("user_id") != user_id:
            continue
        items.append(_history_list_item(item))
        if len(items) >= limit:
            break
    return items


def get_consult_history_detail(user_id: str, history_id: str) -> Optional[Dict[str, Any]]:
    for item in iter_jsonl_reverse(_history_path()):
        if item.get("user_id") == user_id and item.get("history_id") == history_id:
            return {
                "history_id": item.get("history_id"),
                "created_at": item.get("created_at"),
                "question": item.get("question") or "",
                "brief_answer": item.get("brief_answer") or "",
                "answer": item.get("answer") or "",
                "intent": item.get("intent") or {},
                "profile": item.get("profile") or {},
                "module_summaries": item.get("module_summaries") or {},
                "ai": item.get("ai") or {},
                "workspace": item.get("workspace") or None,
            }
    return None


def list_recent_consult_activity(limit: int = 50) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for item in iter_jsonl_reverse(_history_path()):
        intent = item.get("intent") if isinstance(item.get("intent"), dict) else {}
        items.append({
            "history_id": item.get("history_id"),
            "user_id": item.get("user_id"),
            "created_at": item.get("created_at"),
            "question": item.get("question") or "",
            "brief_answer": item.get("brief_answer") or "",
            "modules": intent.get("modules") or [],
            "matter_type": intent.get("matter_type") or "通用",
            "purpose": intent.get("purpose") or "通用",
        })
        if len(items) >= limit:
            break
    return items


def build_consult_activity_summary(limit: int = 200) -> Dict[str, Any]:
    entries = read_jsonl(_history_path())
    recent = list_recent_consult_activity(limit=min(limit, 50))
    module_counter: Counter[str] = Counter()
    purpose_counter: Counter[str] = Counter()
    daily_counter: Counter[str] = Counter()
    recent_user_counter: Counter[str] = Counter()

    for item in entries[-limit:]:
        created_at = str(item.get("created_at") or "")
        if "T" in created_at:
            daily_counter[created_at.split("T", 1)[0]] += 1
        intent = item.get("intent") if isinstance(item.get("intent"), dict) else {}
        for module_name in intent.get("modules") or []:
            module_counter[str(module_name)] += 1
        purpose_counter[str(intent.get("purpose") or "通用")] += 1
        recent_user_counter[str(item.get("user_id") or "")] += 1

    return {
        "total_consults": len(entries),
        "recent_activity": recent,
        "module_breakdown": [{"name": key, "count": value} for key, value in module_counter.most_common()],
        "purpose_breakdown": [{"name": key, "count": value} for key, value in purpose_counter.most_common()],
        "daily_breakdown": [{"date": key, "count": daily_counter[key]} for key in sorted(daily_counter.keys(), reverse=True)[:14]],
        "active_users": [{"user_id": key, "count": value} for key, value in recent_user_counter.most_common(10) if key],
    }
