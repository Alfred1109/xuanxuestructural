"""Contextual followups for a saved consultation."""

import json
from typing import Any, Dict, List

from ..consult_history import (
    append_consult_followup,
    get_consult_followup_by_request_id,
    get_owned_consult_history,
    list_consult_followups,
)
from ..llm_helper import llm_helper
from .idempotency import request_fingerprint, request_id_lock
from .service import IdempotencyConflict


class ConsultHistoryNotFound(Exception):
    """The requested history does not exist or is not owned by the caller."""


class FollowupAIUnavailable(Exception):
    """No usable AI answer was produced, so the followup was not persisted."""


def _build_followup_context(
    history: Dict[str, Any],
    previous_followups: List[Dict[str, Any]],
) -> str:
    consultation = history.get("consultation") if isinstance(history.get("consultation"), dict) else {}
    context = {
        "原始问题": history.get("question") or "",
        "原始结论": consultation.get("answer") or history.get("answer") or "",
        "原始资料": consultation.get("profile") or history.get("profile") or {},
        "事项类型与用途": consultation.get("intent") or history.get("intent") or {},
        "各模块摘要": consultation.get("module_summaries") or history.get("module_summaries") or {},
        "此前追问": previous_followups,
    }
    return (
        "以下为服务端保存的本次问事及追问记录，请以此为上下文回答，不要虚构缺失信息：\n"
        + json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    )


def get_consultation_followups(user_id: str, history_id: str) -> List[Dict[str, Any]]:
    if get_owned_consult_history(user_id, history_id) is None:
        raise ConsultHistoryNotFound(history_id)
    return list_consult_followups(user_id, history_id)


def create_consultation_followup(
    user_id: str,
    history_id: str,
    question: str,
    request_id: str | None = None,
) -> Dict[str, Any]:
    fingerprint_payload = {"history_id": history_id, "question": question}
    fingerprint = request_fingerprint(fingerprint_payload) if request_id else None

    def create_and_store() -> Dict[str, Any]:
        history = get_owned_consult_history(user_id, history_id)
        if history is None:
            raise ConsultHistoryNotFound(history_id)

        previous_followups = list_consult_followups(user_id, history_id)
        context = _build_followup_context(history, previous_followups)
        try:
            answer = llm_helper.chat(question, context)
        except Exception as exc:
            raise FollowupAIUnavailable() from exc
        if not isinstance(answer, str) or not answer.strip():
            raise FollowupAIUnavailable()

        return append_consult_followup(
            user_id,
            history_id,
            question,
            answer.strip(),
            request_id=request_id,
            request_fingerprint=fingerprint,
        )

    if not request_id:
        return create_and_store()

    with request_id_lock("followup", user_id, request_id):
        history = get_owned_consult_history(user_id, history_id)
        if history is None:
            raise ConsultHistoryNotFound(history_id)
        existing = get_consult_followup_by_request_id(user_id, request_id)
        if existing is not None:
            existing_fingerprint = existing.get("request_fingerprint")
            if not isinstance(existing_fingerprint, str) or not existing_fingerprint:
                existing_fingerprint = request_fingerprint({
                    "history_id": existing.get("history_id"),
                    "question": existing.get("question") or "",
                })
            if existing_fingerprint != fingerprint:
                raise IdempotencyConflict()
            return {key: existing.get(key) for key in ("followup_id", "question", "answer", "created_at")}
        return create_and_store()
