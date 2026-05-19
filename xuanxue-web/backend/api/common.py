from datetime import datetime, timezone
from os import getenv
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


SCHEMA_VERSION = "1.1"

AI_RUNTIME_STATE = {
    "last_error": None,
    "last_error_at": None,
}


def build_meta(request: Optional[Request] = None) -> Dict[str, Any]:
    """统一返回元信息，便于追踪与解析。"""
    request_id = None
    if request is not None:
        request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = str(uuid4())
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_id": request_id,
    }


def success_response(data: Any, request: Optional[Request] = None, **extra_fields: Any) -> Dict[str, Any]:
    """统一成功响应外壳。"""
    payload: Dict[str, Any] = {
        "success": True,
        "data": data,
        "meta": build_meta(request),
    }
    payload.update(extra_fields)
    return payload


def default_error_code(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
        500: "internal_error",
        502: "upstream_error",
        503: "service_unavailable",
        504: "gateway_timeout",
    }
    return mapping.get(status_code, "server_error" if status_code >= 500 else "client_error")


def normalize_error_detail(detail: Any, status_code: int) -> Dict[str, Any]:
    if isinstance(detail, dict):
        code = str(detail.get("code") or default_error_code(status_code))
        message = str(detail.get("message") or detail.get("detail") or "请求失败")
        retryable = bool(detail.get("retryable")) if "retryable" in detail else status_code >= 500
        details = detail.get("details")
    else:
        code = default_error_code(status_code)
        message = str(detail) if detail else "请求失败"
        retryable = status_code >= 500
        details = None
    return {
        "code": code,
        "message": message,
        "retryable": retryable,
        "details": details,
    }


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    retryable: bool,
    details: Any = None,
) -> JSONResponse:
    safe_details = jsonable_encoder(details) if details is not None else None
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "details": safe_details,
            },
            "meta": build_meta(request),
        },
    )


def mark_ai_failure(error_message: str) -> None:
    AI_RUNTIME_STATE["last_error"] = error_message
    AI_RUNTIME_STATE["last_error_at"] = datetime.now().isoformat(timespec="seconds")


def mark_ai_success() -> None:
    AI_RUNTIME_STATE["last_error"] = None
    AI_RUNTIME_STATE["last_error_at"] = None


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(
        request=request,
        status_code=422,
        code="validation_error",
        message="请求参数校验失败",
        retryable=False,
        details=exc.errors(),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    normalized = normalize_error_detail(exc.detail, exc.status_code)
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=normalized["code"],
        message=normalized["message"],
        retryable=normalized["retryable"],
        details=normalized["details"],
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    return error_response(
        request=request,
        status_code=500,
        code="internal_error",
        message="服务内部错误",
        retryable=True,
        details={"type": exc.__class__.__name__},
    )


def configure_cors(app) -> None:
    cors_origins = [
        origin.strip()
        for origin in getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost,http://127.0.0.1,http://localhost:8003,http://127.0.0.1:8003",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
