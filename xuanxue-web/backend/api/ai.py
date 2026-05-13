import base64
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Form, HTTPException, Path, Query, Request, UploadFile
from pydantic import BaseModel, Field

from core.bazi_advanced import get_advanced_analysis
from core.bazi_core import BaZiChart
from core.consult.summarizers import generate_simple_analysis
from core.decision.kernel import build_visual_rule_scores
from core.llm_helper import llm_helper
from core.qimen import divine_qimen
from core.zeri import get_today_fortune

from .bazi import BaZiRequest
from .common import AI_RUNTIME_STATE, mark_ai_failure, mark_ai_success, success_response
from .divination import LiuYaoRequest, QiMenRequest, get_liuyao_question, get_qimen_payload
from .divination import divine as liuyao_divine


router = APIRouter()


class AIChatRequest(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    context: Optional[str] = Field("", max_length=2000)


@router.post("/api/ai/visual-insight")
async def ai_visual_insight(
    request: Request,
    mode: str = Form(...),
    question: str = Form(""),
    location: str = Form(""),
    scene_type: str = Form("generic"),
    consent: bool = Form(False),
):
    """图片辅助分析：空间/风水观察、手相参考、面相参考。"""
    try:
        normalized_mode = (mode or "").strip().lower()
        if normalized_mode not in {"space", "palm", "face"}:
            raise HTTPException(status_code=400, detail="mode 仅支持 space / palm / face")

        if normalized_mode in {"palm", "face"} and not consent:
            raise HTTPException(status_code=400, detail="手相/面相分析前需要明确勾选授权与免责声明")

        if not llm_helper.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "ai_unconfigured",
                    "message": "AI服务未配置，请设置ARK_API_KEY，必要时可额外设置ARK_VISION_MODEL",
                    "retryable": False,
                },
            )

        uploaded_files: list[UploadFile] = []
        form = await request.form()
        maybe_multi = form.getlist("images")
        maybe_single = form.get("image")

        for item in maybe_multi:
            if isinstance(item, UploadFile):
                uploaded_files.append(item)
        if isinstance(maybe_single, UploadFile):
            uploaded_files.append(maybe_single)

        uploaded_files = [item for item in uploaded_files if item is not None]
        if not uploaded_files:
            raise HTTPException(status_code=400, detail="请至少上传一张图片")

        if normalized_mode == "space":
            if len(uploaded_files) > 4:
                raise HTTPException(status_code=400, detail="空间观察最多支持 4 张图片")
        else:
            uploaded_files = uploaded_files[:1]

        image_data_urls: list[str] = []
        image_names: list[str] = []
        for uploaded in uploaded_files:
            content_type = uploaded.content_type or ""
            if not content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="仅支持上传图片文件")

            raw = await uploaded.read()
            if not raw:
                raise HTTPException(status_code=400, detail="上传的图片为空")
            if len(raw) > 8 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="图片过大，请控制在 8MB 以内")

            image_data_urls.append("data:{mime};base64,{payload}".format(
                mime=content_type,
                payload=base64.b64encode(raw).decode("ascii"),
            ))
            image_names.append(uploaded.filename or "uploaded-image")

        structure = llm_helper.extract_visual_structure(
            image_data_urls=image_data_urls,
            mode=normalized_mode,
            question=question,
            location=location,
            scene_type=scene_type,
        )
        analysis = llm_helper.analyze_visual_insight(
            image_data_urls=image_data_urls,
            mode=normalized_mode,
            question=question,
            location=location,
            scene_type=scene_type,
        )
        if not analysis:
            mark_ai_failure("visual_insight_empty")
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "ai_upstream_empty",
                    "message": "视觉分析暂时不可用，请检查 ARK_VISION_MODEL 是否支持图片理解",
                    "retryable": True,
                },
            )

        mark_ai_success()
        mode_labels = {
            "space": "空间 / 风水观察",
            "palm": "手相参考",
            "face": "面相参考",
        }
        visual_summary = {
            "mode": normalized_mode,
            "structure": structure or {},
        }
        rule_scores = build_visual_rule_scores(visual_summary)
        return success_response(
            {
                "mode": normalized_mode,
                "mode_label": mode_labels[normalized_mode],
                "analysis": analysis,
                "disclaimer": "结果仅作文化娱乐与环境观察参考，不构成身份识别、医疗、法律或确定性人生判断。",
                "image_name": f"{len(image_names)} 张图片" if len(image_names) > 1 else image_names[0],
                "image_names": image_names,
                "location": location.strip(),
                "scene_type": scene_type.strip(),
                "structure": structure or {},
                "rule_scores": rule_scores,
            },
            request=request,
            ai_enabled=True,
            ai_enhanced=True,
        )
    except HTTPException:
        raise
    except Exception as exc:
        mark_ai_failure(f"visual_insight_exception: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"图片分析失败: {str(exc)}")


@router.post("/api/ai/enhance-liuyao")
async def ai_enhance_liuyao(
    request: Request,
    question: Optional[str] = Query(None, max_length=500),
    payload: Optional[LiuYaoRequest] = Body(default=None),
):
    """AI增强六爻占卜"""
    try:
        result = liuyao_divine(get_liuyao_question(question, payload))
        ai_enabled = llm_helper.is_available()
        ai_enhanced = False
        ai_message = "AI服务未配置，已返回基础解读"

        if ai_enabled:
            ai_interpretation = llm_helper.enhance_liuyao_interpretation(result)
            if ai_interpretation:
                result["ai_interpretation"] = ai_interpretation
                ai_enhanced = True
                ai_message = ""
                mark_ai_success()
            else:
                ai_message = "AI服务暂时不可用，已返回基础解读"
                mark_ai_failure("enhance_liuyao_empty")

        result["ai"] = {
            "enabled": ai_enabled,
            "enhanced": ai_enhanced,
            "message": ai_message,
        }
        return success_response(
            result,
            request=request,
            ai_enabled=ai_enabled,
            ai_enhanced=ai_enhanced,
            ai_message=ai_message,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(exc)}")


@router.post("/api/ai/enhance-qimen")
async def ai_enhance_qimen(
    request: Request,
    year: Optional[int] = Query(None, ge=1900, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    day: Optional[int] = Query(None, ge=1, le=31),
    hour: Optional[int] = Query(None, ge=0, le=23),
    minute: Optional[int] = Query(None, ge=0, le=59),
    matter_type: Optional[str] = Query(None, min_length=1, max_length=20),
    payload: Optional[QiMenRequest] = Body(default=None),
):
    """AI增强奇门遁甲占卜"""
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
        ai_enabled = llm_helper.is_available()
        ai_enhanced = False
        ai_message = "AI服务未配置，已返回基础解读"

        if ai_enabled:
            ai_interpretation = llm_helper.enhance_qimen_interpretation(result, final_payload.matter_type)
            if ai_interpretation:
                result["ai_interpretation"] = ai_interpretation
                ai_enhanced = True
                ai_message = ""
                mark_ai_success()
            else:
                ai_message = "AI服务暂时不可用，已返回基础解读"
                mark_ai_failure("enhance_qimen_empty")

        result["ai"] = {
            "enabled": ai_enabled,
            "enhanced": ai_enhanced,
            "message": ai_message,
        }
        return success_response(
            result,
            request=request,
            ai_enabled=ai_enabled,
            ai_enhanced=ai_enhanced,
            ai_message=ai_message,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(exc)}")


@router.post("/api/ai/chat")
async def ai_chat(
    request: Request,
    question: Optional[str] = Query(None, min_length=1, max_length=500),
    context: Optional[str] = Query(None, max_length=2000),
    payload: Optional[AIChatRequest] = Body(default=None),
):
    """AI对话接口"""
    try:
        body_question = payload.question.strip() if payload and payload.question else ""
        body_context = payload.context if payload else ""
        final_question = (question or body_question).strip()
        final_context = context if context is not None else body_context

        if not final_question:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "missing_question",
                    "message": "question 不能为空",
                    "retryable": False,
                },
            )

        if not llm_helper.is_available():
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "ai_unconfigured",
                    "message": "AI服务未配置，请设置ARK_API_KEY环境变量",
                    "retryable": False,
                },
            )

        response = llm_helper.chat(final_question, final_context if final_context else None)
        if not response:
            mark_ai_failure("chat_empty_response")
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "ai_upstream_empty",
                    "message": "AI服务暂时不可用",
                    "retryable": True,
                },
            )

        mark_ai_success()
        return success_response(
            {
                "question": final_question,
                "answer": response,
                "context": final_context or "",
            },
            request=request,
        )
    except HTTPException:
        raise
    except Exception as exc:
        mark_ai_failure(f"chat_exception: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"对话错误: {str(exc)}")


@router.post("/api/ai/enhance-bazi")
async def ai_enhance_bazi(payload: BaZiRequest, request: Request):
    """AI增强八字分析"""
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
        ai_enabled = llm_helper.is_available()
        ai_enhanced = False
        ai_message = "AI服务未配置，已返回基础解读"

        if ai_enabled:
            ai_analysis = llm_helper.enhance_bazi_analysis(result)
            if ai_analysis:
                result["ai_analysis"] = ai_analysis
                ai_enhanced = True
                ai_message = ""
                mark_ai_success()
            else:
                ai_message = "AI服务暂时不可用，已返回基础解读"
                mark_ai_failure("enhance_bazi_empty")

        result["ai"] = {
            "enabled": ai_enabled,
            "enhanced": ai_enhanced,
            "message": ai_message,
        }
        return success_response(
            result,
            request=request,
            ai_enabled=ai_enabled,
            ai_enhanced=ai_enhanced,
            ai_message=ai_message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(exc)}")


@router.get("/api/ai/status")
async def ai_status(request: Request):
    """检查AI服务状态"""
    available = llm_helper.is_available()
    if not available:
        status = "unconfigured"
        message = "AI服务未配置"
    elif AI_RUNTIME_STATE["last_error"]:
        status = "degraded"
        message = "AI服务可用但最近一次请求失败"
    else:
        status = "available"
        message = "AI服务正常"

    return success_response(
        {
            "status": status,
            "available": available,
            "model": llm_helper.model if available else None,
            "message": message,
            "last_error": AI_RUNTIME_STATE["last_error"],
            "last_error_at": AI_RUNTIME_STATE["last_error_at"],
        },
        request=request,
    )


@router.get("/api/ai/enhance-zeri/today")
async def ai_enhance_zeri_today(
    request: Request,
    purpose: str = Query("通用", min_length=1, max_length=20),
):
    """获取服务端今日日期的AI增强择日分析"""
    today = datetime.now()
    return await ai_enhance_zeri(request, today.year, today.month, today.day, purpose)


@router.get("/api/ai/enhance-zeri/{year}/{month}/{day}")
async def ai_enhance_zeri(
    request: Request,
    year: int = Path(..., ge=1900, le=2100),
    month: int = Path(..., ge=1, le=12),
    day: int = Path(..., ge=1, le=31),
    purpose: str = Query("通用", min_length=1, max_length=20),
):
    """AI增强择日分析"""
    try:
        fortune = get_today_fortune(year, month, day)
        ai_enabled = llm_helper.is_available()
        ai_enhanced = False
        ai_message = "AI服务未配置，已返回基础解读"

        if ai_enabled:
            ai_advice = llm_helper.enhance_zeri_advice(fortune, purpose)
            if ai_advice:
                fortune["ai_advice"] = ai_advice
                ai_enhanced = True
                ai_message = ""
                mark_ai_success()
            else:
                ai_message = "AI服务暂时不可用，已返回基础解读"
                mark_ai_failure("enhance_zeri_empty")

        fortune["ai"] = {
            "enabled": ai_enabled,
            "enhanced": ai_enhanced,
            "message": ai_message,
        }
        return success_response(
            fortune,
            request=request,
            ai_enabled=ai_enabled,
            ai_enhanced=ai_enhanced,
            ai_message=ai_message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(exc)}")
