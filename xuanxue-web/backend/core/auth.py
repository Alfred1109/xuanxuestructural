"""
账号与会话管理
Lightweight local auth backed by JSON files.
"""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import HTTPException, Request

from .runtime.store import read_json_file, resolve_runtime_path, update_json_file, write_json_file


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_ITERATIONS = 120000
SESSION_TTL_DAYS = 30


def _users_path():
    return resolve_runtime_path("USER_STORE_PATH", "users.json")


def _sessions_path():
    return resolve_runtime_path("SESSION_STORE_PATH", "sessions.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _read_users() -> List[Dict[str, Any]]:
    payload = read_json_file(_users_path(), {"users": []})
    users = payload.get("users") if isinstance(payload, dict) else []
    return users if isinstance(users, list) else []


def _write_users(users: List[Dict[str, Any]]) -> None:
    write_json_file(_users_path(), {"users": users})


def _read_sessions() -> List[Dict[str, Any]]:
    payload = read_json_file(_sessions_path(), {"sessions": []})
    sessions = payload.get("sessions") if isinstance(payload, dict) else []
    return sessions if isinstance(sessions, list) else []


def _write_sessions(sessions: List[Dict[str, Any]]) -> None:
    write_json_file(_sessions_path(), {"sessions": sessions})


def _extract_users(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    users = payload.get("users") if isinstance(payload, dict) else []
    return users if isinstance(users, list) else []


def _extract_sessions(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    sessions = payload.get("sessions") if isinstance(payload, dict) else []
    return sessions if isinstance(sessions, list) else []


def _cleanup_expired_sessions(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    cleaned: List[Dict[str, Any]] = []
    for session in sessions:
        expires_at = session.get("expires_at")
        if not expires_at:
            continue
        try:
            expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if expires_dt > now:
            cleaned.append(session)
    return cleaned


def _hash_password(password: str, salt_hex: Optional[str] = None) -> Tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return salt.hex(), derived.hex()


def _verify_password(password: str, user: Dict[str, Any]) -> bool:
    salt_hex = str(user.get("password_salt") or "")
    password_hash = str(user.get("password_hash") or "")
    if not salt_hex or not password_hash:
        return False
    _, candidate_hash = _hash_password(password, salt_hex=salt_hex)
    return hmac.compare_digest(candidate_hash, password_hash)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize_email(email)
    for user in _read_users():
        if _normalize_email(str(user.get("email") or "")) == normalized:
            return user
    return None


def _find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    for user in _read_users():
        if user.get("user_id") == user_id:
            return user
    return None


def _sanitize_birth(profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    birth = profile.get("birth")
    if not isinstance(birth, dict):
        return None
    result = {
        "year": birth.get("year"),
        "month": birth.get("month"),
        "day": birth.get("day"),
        "hour": birth.get("hour"),
        "minute": birth.get("minute"),
    }
    if all(value is None for value in result.values()):
        return None
    return result


def public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    profile = user.get("profile") if isinstance(user.get("profile"), dict) else {}
    display_name = str(user.get("display_name") or profile.get("display_name") or "").strip()
    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "display_name": display_name or _normalize_email(str(user.get("email") or "")).split("@")[0],
        "profile": {
            "gender": profile.get("gender"),
            "birth": _sanitize_birth(profile),
            "location": profile.get("location") or "",
            "consult_presets": profile.get("consult_presets") if isinstance(profile.get("consult_presets"), list) else [],
        },
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def _validate_email(email: str) -> str:
    normalized = _normalize_email(email)
    if not normalized or not EMAIL_PATTERN.match(normalized):
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "请输入有效的邮箱地址", "retryable": False},
        )
    return normalized


def _validate_password(password: str) -> str:
    if len(password or "") < 8:
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "密码至少需要 8 位", "retryable": False},
        )
    return password


def _validate_gender(gender: Optional[str]) -> Optional[str]:
    if gender in (None, ""):
        return None
    if gender not in ("男", "女"):
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "性别仅支持 男 或 女", "retryable": False},
        )
    return gender


def _build_profile_updates(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "gender": _validate_gender(data.get("gender")),
        "birth": {
            "year": data.get("year"),
            "month": data.get("month"),
            "day": data.get("day"),
            "hour": data.get("hour"),
            "minute": data.get("minute"),
        },
        "location": (data.get("location") or "").strip(),
    }


def _normalize_consult_preset(data: Dict[str, Any]) -> Dict[str, Any]:
    name = str(data.get("name") or "").strip()
    if not name:
        raise HTTPException(
            status_code=400,
            detail={"code": "bad_request", "message": "常用条件名称不能为空", "retryable": False},
        )
    question = str(data.get("question") or "").strip()
    return {
        "preset_id": str(data.get("preset_id") or str(uuid4())),
        "name": name[:40],
        "question": question[:500],
        "year": data.get("year"),
        "month": data.get("month"),
        "day": data.get("day"),
        "hour": data.get("hour"),
        "minute": data.get("minute"),
        "gender": _validate_gender(data.get("gender")),
        "location": str(data.get("location") or "").strip()[:80],
        "is_default": bool(data.get("is_default")),
        "updated_at": _now_iso(),
    }


def create_session(user_id: str) -> Dict[str, Any]:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)).isoformat(timespec="seconds")

    def updater(payload: Dict[str, Any]) -> Dict[str, Any]:
        sessions = _cleanup_expired_sessions(_extract_sessions(payload))
        sessions.append(
            {
                "session_id": str(uuid4()),
                "user_id": user_id,
                "token_hash": _hash_token(token),
                "created_at": _now_iso(),
                "expires_at": expires_at,
            }
        )
        return {"sessions": sessions}

    update_json_file(_sessions_path(), {"sessions": []}, updater)
    return {
        "token": token,
        "expires_at": expires_at,
    }


def register_user(email: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    normalized_email = _validate_email(email)
    _validate_password(password)
    now = _now_iso()
    password_salt, password_hash = _hash_password(password)
    safe_display_name = (display_name or "").strip() or normalized_email.split("@")[0]
    user = {
        "user_id": str(uuid4()),
        "email": normalized_email,
        "display_name": safe_display_name,
        "password_salt": password_salt,
        "password_hash": password_hash,
        "profile": {
            "gender": None,
            "birth": None,
            "location": "",
        },
        "created_at": now,
        "updated_at": now,
    }

    def updater(payload: Dict[str, Any]) -> Dict[str, Any]:
        users = _extract_users(payload)
        if any(_normalize_email(str(item.get("email") or "")) == normalized_email for item in users):
            raise HTTPException(
                status_code=409,
                detail={"code": "conflict", "message": "该邮箱已注册", "retryable": False},
            )
        users.append(user)
        return {"users": users}

    update_json_file(_users_path(), {"users": []}, updater)

    session = create_session(user["user_id"])
    return {
        "user": public_user(user),
        "token": session["token"],
        "expires_at": session["expires_at"],
    }


def login_user(email: str, password: str) -> Dict[str, Any]:
    normalized_email = _validate_email(email)
    user = _find_user_by_email(normalized_email)
    if not user or not _verify_password(password, user):
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "账号或密码不正确", "retryable": False},
        )

    session = create_session(str(user.get("user_id")))
    return {
        "user": public_user(user),
        "token": session["token"],
        "expires_at": session["expires_at"],
    }


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None

    def updater(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"sessions": _cleanup_expired_sessions(_extract_sessions(payload))}

    session_payload = update_json_file(_sessions_path(), {"sessions": []}, updater)
    sessions = _extract_sessions(session_payload)
    token_hash = _hash_token(token)
    for session in sessions:
        if hmac.compare_digest(str(session.get("token_hash") or ""), token_hash):
            user = _find_user_by_id(str(session.get("user_id") or ""))
            if user:
                return user
    return None


def logout_session(token: str) -> bool:
    if not token:
        return False
    token_hash = _hash_token(token)
    changed = False

    def updater(payload: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal changed
        sessions = _cleanup_expired_sessions(_extract_sessions(payload))
        remaining = [session for session in sessions if str(session.get("token_hash") or "") != token_hash]
        changed = len(remaining) != len(sessions)
        return {"sessions": remaining}

    update_json_file(_sessions_path(), {"sessions": []}, updater)
    return changed


def update_user_account(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    matched_user: Optional[Dict[str, Any]] = None

    def updater(payload: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal matched_user
        users = _extract_users(payload)

        for user in users:
            if user.get("user_id") != user_id:
                continue

            display_name = updates.get("display_name")
            if display_name is not None:
                display_name = str(display_name).strip()
                if not display_name:
                    raise HTTPException(
                        status_code=400,
                        detail={"code": "bad_request", "message": "昵称不能为空", "retryable": False},
                    )
                user["display_name"] = display_name

            new_password = updates.get("new_password")
            if new_password:
                current_password = str(updates.get("current_password") or "")
                if not current_password or not _verify_password(current_password, user):
                    raise HTTPException(
                        status_code=401,
                        detail={"code": "unauthorized", "message": "当前密码不正确", "retryable": False},
                    )
                _validate_password(str(new_password))
                password_salt, password_hash = _hash_password(str(new_password))
                user["password_salt"] = password_salt
                user["password_hash"] = password_hash

            profile_updates = _build_profile_updates(updates)
            profile = user.get("profile") if isinstance(user.get("profile"), dict) else {}
            profile["gender"] = profile_updates["gender"]
            profile["location"] = profile_updates["location"]
            birth = profile_updates["birth"]
            profile["birth"] = birth if any(value is not None for value in birth.values()) else None
            profile["consult_presets"] = profile.get("consult_presets") if isinstance(profile.get("consult_presets"), list) else []
            user["profile"] = profile
            user["updated_at"] = _now_iso()
            matched_user = user
            break

        if matched_user is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": "账号不存在", "retryable": False},
            )
        return {"users": users}

    update_json_file(_users_path(), {"users": []}, updater)
    return public_user(matched_user)


def list_user_consult_presets(user_id: str) -> List[Dict[str, Any]]:
    user = _find_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "账号不存在", "retryable": False},
        )
    profile = user.get("profile") if isinstance(user.get("profile"), dict) else {}
    presets = profile.get("consult_presets") if isinstance(profile.get("consult_presets"), list) else []
    return presets


def save_user_consult_preset(user_id: str, preset_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized = _normalize_consult_preset(preset_data)
    matched_user: Optional[Dict[str, Any]] = None

    def updater(payload: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal matched_user
        users = _extract_users(payload)

        for user in users:
            if user.get("user_id") != user_id:
                continue
            profile = user.get("profile") if isinstance(user.get("profile"), dict) else {}
            presets = profile.get("consult_presets") if isinstance(profile.get("consult_presets"), list) else []
            updated = False
            if normalized["is_default"]:
                for item in presets:
                    item["is_default"] = False
            for index, item in enumerate(presets):
                if item.get("preset_id") == normalized["preset_id"]:
                    if normalized.get("is_default") is not True and item.get("is_default") is True:
                        normalized["is_default"] = True
                    presets[index] = normalized
                    updated = True
                    break
            if not updated:
                if not presets:
                    normalized["is_default"] = True
                presets.insert(0, normalized)
            if not any(item.get("is_default") for item in presets) and presets:
                presets[0]["is_default"] = True
            profile["consult_presets"] = presets[:12]
            user["profile"] = profile
            user["updated_at"] = _now_iso()
            matched_user = user
            break

        if matched_user is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": "账号不存在", "retryable": False},
            )
        return {"users": users}

    update_json_file(_users_path(), {"users": []}, updater)
    return public_user(matched_user)["profile"]["consult_presets"]


def delete_user_consult_preset(user_id: str, preset_id: str) -> List[Dict[str, Any]]:
    matched_user: Optional[Dict[str, Any]] = None

    def updater(payload: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal matched_user
        users = _extract_users(payload)

        for user in users:
            if user.get("user_id") != user_id:
                continue
            profile = user.get("profile") if isinstance(user.get("profile"), dict) else {}
            presets = profile.get("consult_presets") if isinstance(profile.get("consult_presets"), list) else []
            profile["consult_presets"] = [item for item in presets if item.get("preset_id") != preset_id]
            if profile["consult_presets"] and not any(item.get("is_default") for item in profile["consult_presets"]):
                profile["consult_presets"][0]["is_default"] = True
            user["profile"] = profile
            user["updated_at"] = _now_iso()
            matched_user = user
            break

        if matched_user is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": "账号不存在", "retryable": False},
            )
        return {"users": users}

    update_json_file(_users_path(), {"users": []}, updater)
    return public_user(matched_user)["profile"]["consult_presets"]


def extract_token_from_request(request: Request) -> Optional[str]:
    authorization = str(request.headers.get("authorization") or "").strip()
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        return token or None
    legacy_token = str(request.headers.get("x-session-token") or "").strip()
    return legacy_token or None


def resolve_authenticated_user(request: Request, required: bool = True) -> Optional[Dict[str, Any]]:
    token = extract_token_from_request(request)
    if not token:
        if required:
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthorized", "message": "请先登录", "retryable": False},
            )
        return None

    user = get_user_by_token(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "登录状态已失效，请重新登录", "retryable": False},
        )
    return user
