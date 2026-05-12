"""
运行时存储层
Shared JSONL persistence helpers for runtime data.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


def resolve_runtime_path(env_var: str, default_filename: str) -> Path:
    env_path = os.getenv(env_var)
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parents[2] / "runtime" / default_filename


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_recent_jsonl(path: Path, limit: int = 20) -> List[Dict[str, Any]]:
    if limit <= 0 or not path.exists():
        return []

    entries: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                entries.append(item)
    return entries[-limit:]
