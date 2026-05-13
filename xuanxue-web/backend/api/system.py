from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

from core.auth import resolve_authenticated_user
from core.consult_history import append_consult_history
from core.decision.weight_tuning import (
    DEFAULT_WEIGHT_PRESETS,
    read_weight_tuning_events,
    record_weight_tuning,
    resolve_effective_weight_presets,
)
from core.decision_log import append_feedback_log, read_recent_decision_logs
from core.system_engine import UnifiedConsultRequest, consultation_engine

from .common import success_response


router = APIRouter()


class DecisionFeedbackRequest(BaseModel):
    log_id: str = Field(..., min_length=1, max_length=100)
    outcome: str = Field(..., min_length=1, max_length=50)
    adopted: bool = False
    score: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field("", max_length=2000)


class WeightTuningRequest(BaseModel):
    decision_type: str = Field(..., min_length=1, max_length=50)
    module_weights: Dict[str, float]
    reason: str = Field(..., min_length=1, max_length=1000)

    @field_validator("module_weights")
    @classmethod
    def validate_module_weights(cls, value: Dict[str, float]) -> Dict[str, float]:
        if not value:
            raise ValueError("module_weights cannot be empty")
        for module_name, weight in value.items():
            if weight < 0:
                raise ValueError(f"weight for {module_name} must be non-negative")
        return value


@router.get("/")
async def root(request: Request):
    """API根路径"""
    return success_response(
        {
            "message": "欢迎使用玄学预测系统API",
            "version": "1.0.0",
            "endpoints": {
                "八字排盘": "/api/bazi",
                "梅花易数": "/api/divination/meihua",
                "阳历转农历": "/api/calendar/solar-to-lunar",
                "农历转阳历": "/api/calendar/lunar-to-solar",
                "年份干支": "/api/ganzhi/year",
            },
        },
        request=request,
    )


@router.post("/api/system/consult")
async def system_consult(payload: UnifiedConsultRequest, request: Request):
    """统一玄学问事接口。"""
    try:
        user = resolve_authenticated_user(request, required=True)
        consultation = consultation_engine.consult(payload)
        consultation["account_history"] = append_consult_history(str(user.get("user_id")), consultation)
        return success_response(consultation, request=request)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"请求参数错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"系统问事失败: {str(exc)}")


@router.post("/api/system/feedback")
async def system_feedback(payload: DecisionFeedbackRequest, request: Request):
    """记录一次统一问事结果反馈，供后续复盘调参。"""
    try:
        result = append_feedback_log(payload.model_dump())
        return success_response(result, request=request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"反馈记录失败: {str(exc)}")


@router.get("/api/system/logs")
async def system_logs(request: Request, limit: int = Query(20, ge=1, le=200)):
    """读取最近的统一问事日志与反馈。"""
    try:
        result = read_recent_decision_logs(limit=limit)
        return success_response({"items": result, "count": len(result)}, request=request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"日志读取失败: {str(exc)}")


@router.get("/api/system/weights")
async def system_weights(request: Request):
    """读取当前默认权重、有效权重与最近调权事件。"""
    return success_response(
        {
            "defaults": DEFAULT_WEIGHT_PRESETS,
            "effective": resolve_effective_weight_presets(),
            "recent_events": read_weight_tuning_events(limit=20),
        },
        request=request,
    )


@router.post("/api/system/weights")
async def system_weights_update(payload: WeightTuningRequest, request: Request):
    """记录一次可审计的权重调节事件。"""
    try:
        event = {
            "decision_type": payload.decision_type,
            "module_weights": payload.module_weights,
            "reason": payload.reason,
        }
        result = record_weight_tuning(event)
        return success_response(result, request=request, recorded_event=event)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"权重调节记录失败: {str(exc)}")
