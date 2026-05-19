"""
运行时存储层
Shared JSONL persistence helpers for runtime data.
"""

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX fallback
    msvcrt = None


def resolve_runtime_path(env_var: str, default_filename: str) -> Path:
    env_path = os.getenv(env_var)
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parents[2] / "runtime" / default_filename


def _lock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".lock")


@contextmanager
def runtime_file_lock(path: Path):
    lock_path = _lock_path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        lock_file.seek(0)
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows fallback
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows fallback
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with runtime_file_lock(path):
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    entries: List[Dict[str, Any]] = []
    with runtime_file_lock(path):
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

    with runtime_file_lock(path):
        return _read_json_file_unlocked(path, default)


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with runtime_file_lock(path):
        _write_json_file_unlocked(path, payload)


def update_json_file(path: Path, default: Any, updater: Callable[[Any], Any]) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)
    with runtime_file_lock(path):
        payload = _read_json_file_unlocked(path, default)
        result = updater(payload)
        next_payload = result if result is not None else payload
        _write_json_file_unlocked(path, next_payload)
        return next_payload


def _read_json_file_unlocked(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def _write_json_file_unlocked(path: Path, payload: Any) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    temp_path.replace(path)
