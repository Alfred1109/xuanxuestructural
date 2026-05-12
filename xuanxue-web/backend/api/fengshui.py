from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.fengshui import FengShuiReading

from .common import success_response


router = APIRouter()


class FengShuiRequest(BaseModel):
    question: str = Field("", max_length=500)
    location: str = Field("", max_length=80)
    orientation: str = Field("", max_length=20)
    scene_type: str = Field("generic", max_length=20)
    layout_note: str = Field("", max_length=500)


@router.post("/api/fengshui")
async def calculate_fengshui(payload: FengShuiRequest, request: Request):
    """风水 / 空间评估 API。"""
    try:
        result = FengShuiReading(
            question=payload.question,
            location=payload.location,
            orientation=payload.orientation,
            scene_type=payload.scene_type,
            layout_note=payload.layout_note,
        ).to_dict()
        return success_response(result, request=request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"风水评估失败: {str(exc)}")
