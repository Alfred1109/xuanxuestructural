from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator

from core.auth import (
    delete_user_consult_preset,
    extract_token_from_request,
    login_user,
    list_user_consult_presets,
    logout_session,
    public_user,
    register_user,
    resolve_authenticated_user,
    save_user_consult_preset,
    update_user_account,
)
from core.consult_history import get_consult_history_detail, list_consult_history

from .common import success_response


router = APIRouter()


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=8, max_length=120)
    display_name: Optional[str] = Field(None, max_length=40)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=8, max_length=120)


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=40)
    gender: Optional[str] = Field(None, max_length=1)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    day: Optional[int] = Field(None, ge=1, le=31)
    hour: Optional[int] = Field(None, ge=0, le=23)
    minute: Optional[int] = Field(None, ge=0, le=59)
    location: Optional[str] = Field("", max_length=80)
    current_password: Optional[str] = Field(None, max_length=120)
    new_password: Optional[str] = Field(None, min_length=8, max_length=120)

    @model_validator(mode="after")
    def validate_password_change(self):
        if self.new_password and not self.current_password:
            raise ValueError("修改密码时必须提供当前密码")
        return self


class ConsultPresetRequest(BaseModel):
    preset_id: Optional[str] = Field(None, max_length=100)
    name: str = Field(..., min_length=1, max_length=40)
    question: Optional[str] = Field("", max_length=500)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    day: Optional[int] = Field(None, ge=1, le=31)
    hour: Optional[int] = Field(None, ge=0, le=23)
    minute: Optional[int] = Field(None, ge=0, le=59)
    gender: Optional[str] = Field(None, max_length=1)
    location: Optional[str] = Field("", max_length=80)
    is_default: bool = False


@router.post("/api/auth/register")
async def auth_register(payload: RegisterRequest, request: Request):
    result = register_user(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    return success_response(result, request=request)


@router.post("/api/auth/login")
async def auth_login(payload: LoginRequest, request: Request):
    result = login_user(email=payload.email, password=payload.password)
    return success_response(result, request=request)


@router.post("/api/auth/logout")
async def auth_logout(request: Request):
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail={"code": "unauthorized", "message": "请先登录", "retryable": False})
    logout_session(token)
    return success_response({"logged_out": True}, request=request)


@router.get("/api/auth/me")
async def auth_me(request: Request):
    user = resolve_authenticated_user(request)
    return success_response({"user": public_user(user)}, request=request)


@router.patch("/api/auth/profile")
async def auth_profile_update(payload: ProfileUpdateRequest, request: Request):
    user = resolve_authenticated_user(request)
    updated_user = update_user_account(str(user.get("user_id")), payload.model_dump(exclude_unset=True))
    return success_response({"user": updated_user}, request=request)


@router.get("/api/auth/history")
async def auth_history_list(request: Request, limit: int = Query(20, ge=1, le=100)):
    user = resolve_authenticated_user(request)
    items = list_consult_history(str(user.get("user_id")), limit=limit)
    return success_response({"items": items, "count": len(items)}, request=request)


@router.get("/api/auth/history/{history_id}")
async def auth_history_detail(history_id: str, request: Request):
    user = resolve_authenticated_user(request)
    detail = get_consult_history_detail(str(user.get("user_id")), history_id)
    if detail is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "未找到该历史记录", "retryable": False})
    return success_response({"item": detail}, request=request)


@router.get("/api/auth/consult-presets")
async def auth_consult_preset_list(request: Request):
    user = resolve_authenticated_user(request)
    items = list_user_consult_presets(str(user.get("user_id")))
    return success_response({"items": items, "count": len(items)}, request=request)


@router.post("/api/auth/consult-presets")
async def auth_consult_preset_save(payload: ConsultPresetRequest, request: Request):
    user = resolve_authenticated_user(request)
    items = save_user_consult_preset(str(user.get("user_id")), payload.model_dump())
    return success_response({"items": items, "count": len(items)}, request=request)


@router.delete("/api/auth/consult-presets/{preset_id}")
async def auth_consult_preset_delete(preset_id: str, request: Request):
    user = resolve_authenticated_user(request)
    items = delete_user_consult_preset(str(user.get("user_id")), preset_id)
    return success_response({"items": items, "count": len(items)}, request=request)
