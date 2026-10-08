"""Cross-process idempotency primitives for saved consultation actions."""

import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator

from ..runtime.store import resolve_runtime_path, runtime_file_lock


def request_fingerprint(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@contextmanager
def request_id_lock(scope: str, user_id: str, request_id: str) -> Iterator[None]:
    """Serialize only matching (scope, user, request_id) operations."""
    key = "\0".join((scope, user_id, request_id)).encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    history_path = resolve_runtime_path("CONSULT_HISTORY_PATH", "consult_history.jsonl")
    lock_path = history_path.parent / ".consult-idempotency" / digest
    with runtime_file_lock(Path(lock_path)):
        yield
