from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field, field_validator

from core.liuyao import divine
from core.llm_helper import llm_helper
from core.meihua import divine_meihua
from core.qimen import divine_qimen, get_current_qimen
from core.zeri import find_auspicious_days, get_today_fortune

from .common import mark_ai_failure, mark_ai_success, success_response


router = APIRouter()


class LiuYaoRequest(BaseModel):
    question: Optional[str] = Field("", max_length=500)


class MeiHuaRequest(BaseModel):
    question: Optional[str] = Field("", max_length=500)
    method: str = Field("time", min_length=1, max_length=20)
    numbers: Optional[list[int]] = None

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        if value not in ("time", "number"):
            raise ValueError("method must be 'time' or 'number'")
        return value


class QiMenRequest(BaseModel):
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    matter_type: str = Field("通用", min_length=1, max_length=20)


def get_liuyao_question(question: Optional[str], payload: Optional[LiuYaoRequest]) -> str:
    if question is not None:
        return question.strip()
    if payload and payload.question:
        return payload.question.strip()
    return ""


def get_meihua_payload(
    question: Optional[str],
    method: Optional[str],
    numbers: Optional[str],
    payload: Optional[MeiHuaRequest],
) -> MeiHuaRequest:
    raw_numbers = payload.numbers if payload and payload.numbers is not None else None
    if numbers is not None:
        parsed = [item.strip() for item in numbers.split(",") if item.strip()]
        raw_numbers = [int(item) for item in parsed]

    return MeiHuaRequest(
        question=(question if question is not None else (payload.question if payload else "")) or "",
        method=(method if method is not None else (payload.method if payload else "time")) or "time",
        numbers=raw_numbers,
    )


def get_qimen_payload(
    year: Optional[int],
    month: Optional[int],
    day: Optional[int],
    hour: Optional[int],
    minute: Optional[int],
    matter_type: Optional[str],
    payload: Optional[QiMenRequest],
) -> QiMenRequest:
    if payload is not None:
        return QiMenRequest(
            year=year if year is not None else payload.year,
            month=month if month is not None else payload.month,
            day=day if day is not None else payload.day,
            hour=hour if hour is not None else payload.hour,
            minute=minute if minute is not None else payload.minute,
            matter_type=matter_type if matter_type is not None else payload.matter_type,
        )

    missing_fields = [
        field_name
        for field_name, value in (
            ("year", year),
            ("month", month),
            ("day", day),
            ("hour", hour),
        )
        if value is None
    ]
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "validation_error",
                "message": "请求参数校验失败",
                "retryable": False,
                "details": [
                    {"field": field_name, "message": "Field required"}
                    for field_name in missing_fields
                ],
            },
        )

    return QiMenRequest(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=0 if minute is None else minute,
        matter_type="通用" if matter_type is None else matter_type,
    )


@router.post("/api/divination/liuyao")
async def liuyao_divination(
    request: Request,
    question: Optional[str] = Query(None, max_length=500),
    payload: Optional[LiuYaoRequest] = Body(default=None),
):
    """六爻占卜API"""
    try:
        result = divine(get_liuyao_question(question, payload))
        return success_response(result, request=request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(exc)}")


@router.post("/api/divination/meihua")
async def meihua_divination(
    request: Request,
    question: Optional[str] = Query(None, max_length=500),
    method: Optional[str] = Query(None, min_length=1, max_length=20),
    numbers: Optional[str] = Query(None, max_length=100),
    payload: Optional[MeiHuaRequest] = Body(default=None),
):
    """梅花易数占卜 API"""
    try:
        final_payload = get_meihua_payload(question, method, numbers, payload)
        result = divine_meihua(
            question=final_payload.question or "",
            method=final_payload.method,
            numbers=final_payload.numbers,
        )
        return success_response(result, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"起卦参数错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(exc)}")


@router.post("/api/divination/qimen")
async def qimen_divination(
    request: Request,
    year: Optional[int] = Query(None, ge=1900, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    day: Optional[int] = Query(None, ge=1, le=31),
    hour: Optional[int] = Query(None, ge=0, le=23),
    minute: Optional[int] = Query(None, ge=0, le=59),
    matter_type: Optional[str] = Query(None, min_length=1, max_length=20),
    payload: Optional[QiMenRequest] = Body(default=None),
):
    """奇门遁甲占卜API"""
    try:
        final_payload = get_qimen_payload(year, month, day, hour, minute, matter_type, payload)
        datetime(
            final_payload.year,
            final_payload.month,
            final_payload.day,
            final_payload.hour,
            final_payload.minute,
        )
        result = divine_qimen(
            final_payload.year,
            final_payload.month,
            final_payload.day,
            final_payload.hour,
            final_payload.minute,
            final_payload.matter_type,
        )
        return success_response(result, request=request)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(exc)}")


@router.get("/api/divination/qimen/current")
async def get_current_qimen_api(request: Request, matter_type: str = Query("通用", min_length=1, max_length=20)):
    """获取当前时刻的奇门遁甲盘"""
    try:
        result = get_current_qimen(matter_type)
        return success_response(result, request=request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(exc)}")


@router.get("/api/zeri/today")
async def get_today_fortune_api(request: Request):
    """获取今日运势"""
    try:
        today = datetime.now()
        fortune = get_today_fortune(today.year, today.month, today.day)
        return success_response(fortune, request=request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(exc)}")


@router.get("/api/zeri/date/{year}/{month}/{day}")
async def get_date_fortune_api(
    request: Request,
    year: int = Path(..., ge=1900, le=2100),
    month: int = Path(..., ge=1, le=12),
    day: int = Path(..., ge=1, le=31),
):
    """获取指定日期运势"""
    try:
        fortune = get_today_fortune(year, month, day)
        return success_response(fortune, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(exc)}")


@router.get("/api/zeri/auspicious")
async def find_auspicious_days_api(
    request: Request,
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    purpose: str = Query("通用", min_length=1, max_length=20),
    days: int = Query(30, ge=1, le=366),
):
    """查找吉日"""
    try:
        auspicious_days = find_auspicious_days(year, month, purpose, days)
        return success_response(
            {
                "purpose": purpose,
                "total_count": len(auspicious_days),
                "days": auspicious_days,
            },
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查找错误: {str(exc)}")
