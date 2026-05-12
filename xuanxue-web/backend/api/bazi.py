from datetime import datetime

from fastapi import APIRouter, HTTPException, Path, Request
from pydantic import BaseModel, Field, field_validator

from core.bazi_advanced import get_advanced_analysis
from core.bazi_core import BaZiChart
from core.calendar import lunar_to_solar, solar_to_lunar
from core.consult.summarizers import generate_simple_analysis
from core.ganzhi import get_year_ganzhi

from .common import success_response


router = APIRouter()


class BaZiRequest(BaseModel):
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


class CalendarRequest(BaseModel):
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)


class LunarCalendarRequest(CalendarRequest):
    is_leap: bool = False


@router.post("/api/bazi")
async def calculate_bazi(payload: BaZiRequest, request: Request):
    """八字排盘API（增强版）"""
    try:
        datetime(payload.year, payload.month, payload.day, payload.hour, payload.minute)

        chart = BaZiChart(
            payload.year,
            payload.month,
            payload.day,
            payload.hour,
            payload.minute,
            payload.gender,
        )
        result = chart.to_dict()
        result["analysis"] = generate_simple_analysis(chart)
        result["advanced_analysis"] = get_advanced_analysis(chart)
        return success_response(result, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(exc)}")


@router.post("/api/calendar/solar-to-lunar")
async def convert_solar_to_lunar(payload: CalendarRequest, request: Request):
    """阳历转农历"""
    try:
        lunar = solar_to_lunar(payload.year, payload.month, payload.day)
        return success_response(
            {
                "solar": {
                    "year": payload.year,
                    "month": payload.month,
                    "day": payload.day,
                },
                "lunar": {
                    "year": lunar[0],
                    "month": lunar[1],
                    "day": lunar[2],
                    "is_leap": lunar[3],
                },
            },
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"转换错误: {str(exc)}")


@router.post("/api/calendar/lunar-to-solar")
async def convert_lunar_to_solar(payload: LunarCalendarRequest, request: Request):
    """农历转阳历"""
    try:
        solar = lunar_to_solar(payload.year, payload.month, payload.day, payload.is_leap)
        return success_response(
            {
                "lunar": {
                    "year": payload.year,
                    "month": payload.month,
                    "day": payload.day,
                    "is_leap": payload.is_leap,
                },
                "solar": {
                    "year": solar[0],
                    "month": solar[1],
                    "day": solar[2],
                },
            },
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"转换错误: {str(exc)}")


@router.get("/api/ganzhi/year/{year}")
async def get_year_ganzhi_api(request: Request, year: int = Path(..., ge=1900, le=2100)):
    """获取年份干支"""
    try:
        ganzhi = get_year_ganzhi(year)
        return success_response(
            {
                "year": year,
                "ganzhi": ganzhi,
            },
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"年份错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(exc)}")
