"""
决策日志
Append-only decision log for offline calibration.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from .runtime.store import append_jsonl, read_recent_jsonl, resolve_runtime_path


def _default_log_path():
    return resolve_runtime_path("DECISION_LOG_PATH", "decision_logs.jsonl")


def append_decision_log(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    path = _default_log_path()
    log_id = str(uuid4())
    payload = {
        "log_id": log_id,
        "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot": snapshot,
    }
    append_jsonl(path, payload)
    return {
        "logged": True,
        "log_id": log_id,
        "path": str(path),
    }


def append_feedback_log(feedback: Dict[str, Any]) -> Dict[str, Any]:
    path = _default_log_path()
    feedback_id = str(uuid4())
    payload = {
        "feedback_id": feedback_id,
        "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feedback": feedback,
    }
    append_jsonl(path, payload)
    return {
        "logged": True,
        "feedback_id": feedback_id,
        "path": str(path),
    }


def read_recent_decision_logs(limit: int = 20) -> List[Dict[str, Any]]:
    return read_recent_jsonl(_default_log_path(), limit=limit)
