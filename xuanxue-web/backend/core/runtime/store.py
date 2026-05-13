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


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
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
    return entries


def read_recent_jsonl(path: Path, limit: int = 20) -> List[Dict[str, Any]]:
    if limit <= 0 or not path.exists():
        return []

    return read_jsonl(path)[-limit:]


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    temp_path.replace(path)
