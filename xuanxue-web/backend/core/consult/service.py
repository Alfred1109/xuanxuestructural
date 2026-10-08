"""Application service for executing and persisting unified consultations."""

from copy import deepcopy
from typing import Any, Dict

from core.consult_history import append_consult_history, get_consult_history_by_request_id

from .idempotency import request_fingerprint, request_id_lock


class IdempotencyConflict(Exception):
    """A request ID was reused for a different logical payload."""


def _response_from_history(entry: Dict[str, Any]) -> Dict[str, Any]:
    stored = entry.get("consultation")
    result = deepcopy(stored) if isinstance(stored, dict) else {
        "question": entry.get("question") or "",
        "profile": entry.get("profile") or {},
        "intent": entry.get("intent") or {},
        "module_summaries": entry.get("module_summaries") or {},
        "answer": entry.get("answer") or "",
        "ai": entry.get("ai") or {},
    }
    result["account_history"] = {"saved": True, "history_id": entry.get("history_id")}
    return result


def _stored_fingerprint(entry: Dict[str, Any]) -> str:
    fingerprint = entry.get("request_fingerprint")
    if isinstance(fingerprint, str) and fingerprint:
        return fingerprint
    request_payload = entry.get("request_payload")
    if not isinstance(request_payload, dict):
        return ""
    payload = dict(request_payload)
    payload.pop("request_id", None)
    return request_fingerprint(payload)


def run_consultation(user_id: str, payload: Any, engine: Any) -> Dict[str, Any]:
    request_payload = payload.model_dump(mode="json", exclude_unset=True)
    request_id = payload.request_id
    # request_id is transport metadata, not a form field to restore from history.
    request_payload.pop("request_id", None)
    fingerprint = request_fingerprint(request_payload) if request_id else None

    def execute_and_store() -> Dict[str, Any]:
        consultation = engine.consult(payload)
        account_history = append_consult_history(
            user_id,
            consultation,
            request_payload,
            request_id=request_id,
            request_fingerprint=fingerprint,
        )
        consultation["account_history"] = account_history
        return consultation

    if not request_id:
        return execute_and_store()

    with request_id_lock("consult", user_id, request_id):
        existing = get_consult_history_by_request_id(user_id, request_id)
        if existing is not None:
            if _stored_fingerprint(existing) != fingerprint:
                raise IdempotencyConflict()
            return _response_from_history(existing)
        return execute_and_store()
