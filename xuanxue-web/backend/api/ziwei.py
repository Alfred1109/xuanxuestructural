from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from core.ziwei import ZiWeiChart, analyze_ziwei_chart

from .common import success_response


router = APIRouter()


class ZiWeiRequest(BaseModel):
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    gender: str = Field("男", min_length=1, max_length=1)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        if value not in ("男", "女"):
            raise ValueError("gender must be '男' or '女'")
        return value


@router.post("/api/ziwei")
async def calculate_ziwei(payload: ZiWeiRequest, request: Request):
    """紫微斗数排盘 API。"""
    try:
        datetime(payload.year, payload.month, payload.day, payload.hour, payload.minute)
        chart = ZiWeiChart(
            payload.year,
            payload.month,
            payload.day,
            payload.hour,
            payload.minute,
            payload.gender,
        )
        result = chart.to_dict()
        result["analysis"] = analyze_ziwei_chart(result)
        return success_response(result, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(exc)}")
