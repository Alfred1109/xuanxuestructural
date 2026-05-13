"""
账号问事历史
Per-user consultation history stored in JSONL.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .runtime.store import append_jsonl, read_jsonl, resolve_runtime_path


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
    entries = [
        item for item in read_jsonl(_history_path())
        if item.get("user_id") == user_id
    ]
    items = [_history_list_item(item) for item in reversed(entries)]
    return items[:limit]


def get_consult_history_detail(user_id: str, history_id: str) -> Optional[Dict[str, Any]]:
    for item in reversed(read_jsonl(_history_path())):
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
            }
    return None
