"""
可审计权重调节
Stores explicit tuning events rather than silently changing model behaviour.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from .runtime.store import append_jsonl, read_recent_jsonl, resolve_runtime_path


DEFAULT_WEIGHT_PRESETS = {
    "strategic": {"bazi": 0.29, "ziwei": 0.2, "qimen": 0.16, "fengshui": 0.11, "liuyao": 0.11, "meihua": 0.07, "zeri": 0.06},
    "tactical": {"qimen": 0.26, "liuyao": 0.22, "meihua": 0.15, "fengshui": 0.12, "bazi": 0.09, "ziwei": 0.08, "zeri": 0.08},
    "temporal": {"zeri": 0.35, "qimen": 0.2, "fengshui": 0.12, "liuyao": 0.1, "meihua": 0.07, "bazi": 0.07, "ziwei": 0.09},
    "balanced": {"bazi": 0.18, "ziwei": 0.16, "qimen": 0.19, "fengshui": 0.12, "liuyao": 0.15, "meihua": 0.1, "zeri": 0.1},
}


def _tuning_path():
    return resolve_runtime_path("WEIGHT_TUNING_PATH", "weight_tuning_events.jsonl")


def record_weight_tuning(event: Dict[str, Any]) -> Dict[str, Any]:
    path = _tuning_path()
    event_id = str(uuid4())
    payload = {
        "event_id": event_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
    }
    append_jsonl(path, payload)
    return {
        "recorded": True,
        "event_id": event_id,
        "path": str(path),
    }


def read_weight_tuning_events(limit: int = 200) -> List[Dict[str, Any]]:
    return read_recent_jsonl(_tuning_path(), limit=limit)


def resolve_effective_weight_presets() -> Dict[str, Dict[str, float]]:
    effective = {
        key: dict(value)
        for key, value in DEFAULT_WEIGHT_PRESETS.items()
    }
    for item in read_weight_tuning_events():
        event = item.get("event", {})
        decision_type = event.get("decision_type")
        weights = event.get("module_weights")
        if not decision_type or not isinstance(weights, dict):
            continue
        effective[decision_type] = dict(weights)
    return effective
