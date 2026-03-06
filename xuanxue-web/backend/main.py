"""
玄学预测系统 - FastAPI后端主程序
"""

from fastapi import FastAPI, HTTPException, Query, Path, Request, Body
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Dict
from datetime import datetime, timezone
from os import getenv
from uuid import uuid4

# 导入核心模块
import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.bazi_core import BaZiChart
from core.bazi_advanced import get_advanced_analysis
from core.liuyao import divine
from core.zeri import get_today_fortune, find_auspicious_days
from core.calendar import solar_to_lunar, lunar_to_solar, get_lichun_date
from core.ganzhi import get_year_ganzhi
from core.llm_helper import llm_helper
from core.qimen import divine_qimen, get_current_qimen

app = FastAPI(
    title="玄学预测系统API",
    description="综合性玄学预测平台API",
    version="1.0.0"
)

SCHEMA_VERSION = "1.1"

# 运行时AI状态（用于对外暴露可观测状态）
AI_RUNTIME_STATE = {
    "last_error": None,
    "last_error_at": None
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


# CORS来源配置（逗号分隔），默认仅允许本地前端地址
# 示例: CORS_ALLOW_ORIGINS="https://example.com,https://app.example.com"
cors_origins = [
    origin.strip()
    for origin in getenv("CORS_ALLOW_ORIGINS", "http://localhost:8003,http://127.0.0.1:8003").split(",")
    if origin.strip()
]

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(
        request=request,
        status_code=422,
        code="validation_error",
        message="请求参数校验失败",
        retryable=False,
        details=exc.errors(),
    )


@app.exception_handler(HTTPException)
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return error_response(
        request=request,
        status_code=500,
        code="internal_error",
        message="服务内部错误",
        retryable=True,
        details={"type": exc.__class__.__name__},
    )


# 请求模型
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


class AIChatRequest(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    context: Optional[str] = Field("", max_length=2000)


@app.get("/")
async def root(request: Request):
    """API根路径"""
    return success_response(
        {
            "message": "欢迎使用玄学预测系统API",
            "version": "1.0.0",
            "endpoints": {
                "八字排盘": "/api/bazi",
                "阳历转农历": "/api/calendar/solar-to-lunar",
                "农历转阳历": "/api/calendar/lunar-to-solar",
                "年份干支": "/api/ganzhi/year",
            },
        },
        request=request,
    )


@app.post("/api/bazi")
async def calculate_bazi(payload: BaZiRequest, request: Request):
    """
    八字排盘API（增强版）
    
    参数:
    - year: 出生年份
    - month: 出生月份
    - day: 出生日期
    - hour: 出生小时
    - minute: 出生分钟（可选，默认0）
    - gender: 性别（男/女，默认男）
    
    返回: 完整的八字命盘信息 + 高级分析
    """
    try:
        # 验证日期
        datetime(payload.year, payload.month, payload.day, payload.hour, payload.minute)
        
        # 创建八字命盘
        chart = BaZiChart(
            payload.year,
            payload.month,
            payload.day,
            payload.hour,
            payload.minute,
            payload.gender
        )
        
        # 返回完整信息
        result = chart.to_dict()
        
        # 添加基础分析
        result['analysis'] = generate_simple_analysis(chart)
        
        # 添加高级分析
        result['advanced_analysis'] = get_advanced_analysis(chart)
        
        return success_response(result, request=request)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.post("/api/divination/liuyao")
async def liuyao_divination(request: Request, question: str = Query("", max_length=500)):
    """
    六爻占卜API
    
    参数:
    - question: 占卜的问题（可选）
    
    返回: 卦象和解释
    """
    try:
        result = divine(question)
        return success_response(result, request=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.post("/api/ai/enhance-liuyao")
async def ai_enhance_liuyao(request: Request, question: str = Query("", max_length=500)):
    """
    AI增强六爻占卜
    
    参数:
    - question: 占卜的问题（可选）
    
    返回: 卦象 + AI深度解读
    """
    try:
        result = divine(question)
        ai_enabled = llm_helper.is_available()
        ai_enhanced = False
        ai_message = "AI服务未配置，已返回基础解读"

        if ai_enabled:
            ai_interpretation = llm_helper.enhance_liuyao_interpretation(result)
            if ai_interpretation:
                result['ai_interpretation'] = ai_interpretation
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.post("/api/divination/qimen")
async def qimen_divination(
    request: Request,
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    matter_type: str = Query("通用", min_length=1, max_length=20)
):
    """
    奇门遁甲占卜API
    
    参数:
    - year, month, day, hour, minute: 时间
    - matter_type: 事项类型（求财、求职、婚姻、出行、诉讼、疾病、学业、通用）
    
    返回: 奇门遁甲盘和分析
    """
    try:
        datetime(year, month, day, hour, minute)
        result = divine_qimen(year, month, day, hour, minute, matter_type)
        return success_response(result, request=request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.get("/api/divination/qimen/current")
async def get_current_qimen_api(request: Request, matter_type: str = Query("通用", min_length=1, max_length=20)):
    """
    获取当前时刻的奇门遁甲盘
    
    参数:
    - matter_type: 事项类型（求财、求职、婚姻、出行、诉讼、疾病、学业、通用）
    
    返回: 当前时刻的奇门遁甲盘和分析
    """
    try:
        result = get_current_qimen(matter_type)
        return success_response(result, request=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.post("/api/ai/enhance-qimen")
async def ai_enhance_qimen(
    request: Request,
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(..., ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    matter_type: str = Query("通用", min_length=1, max_length=20)
):
    """
    AI增强奇门遁甲占卜
    
    参数:
    - year, month, day, hour, minute: 时间
    - matter_type: 事项类型
    
    返回: 奇门遁甲盘 + AI深度解读
    """
    try:
        datetime(year, month, day, hour, minute)
        result = divine_qimen(year, month, day, hour, minute, matter_type)
        ai_enabled = llm_helper.is_available()
        ai_enhanced = False
        ai_message = "AI服务未配置，已返回基础解读"

        if ai_enabled:
            ai_interpretation = llm_helper.enhance_qimen_interpretation(result, matter_type)
            if ai_interpretation:
                result['ai_interpretation'] = ai_interpretation
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.post("/api/calendar/solar-to-lunar")
async def convert_solar_to_lunar(payload: CalendarRequest, request: Request):
    """阳历转农历"""
    try:
        lunar = solar_to_lunar(payload.year, payload.month, payload.day)
        return success_response(
            {
                "solar": {
                    "year": payload.year,
                    "month": payload.month,
                    "day": payload.day
                },
                "lunar": {
                    "year": lunar[0],
                    "month": lunar[1],
                    "day": lunar[2],
                    "is_leap": lunar[3]
                }
            },
            request=request,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换错误: {str(e)}")


@app.get("/api/ganzhi/year/{year}")
async def get_year_ganzhi_api(request: Request, year: int = Path(..., ge=1900, le=2100)):
    """获取年份干支"""
    try:
        ganzhi = get_year_ganzhi(year)
        return success_response(
            {
                "year": year,
                "ganzhi": ganzhi
            },
            request=request,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"年份错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/zeri/today")
async def get_today_fortune_api(request: Request):
    """获取今日运势"""
    try:
        today = datetime.now()
        fortune = get_today_fortune(today.year, today.month, today.day)
        return success_response(fortune, request=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/zeri/date/{year}/{month}/{day}")
async def get_date_fortune_api(
    request: Request,
    year: int = Path(..., ge=1900, le=2100),
    month: int = Path(..., ge=1, le=12),
    day: int = Path(..., ge=1, le=31)
):
    """获取指定日期运势"""
    try:
        fortune = get_today_fortune(year, month, day)
        return success_response(fortune, request=request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/ai/enhance-zeri/{year}/{month}/{day}")
async def ai_enhance_zeri(
    request: Request,
    year: int = Path(..., ge=1900, le=2100),
    month: int = Path(..., ge=1, le=12),
    day: int = Path(..., ge=1, le=31),
    purpose: str = Query("通用", min_length=1, max_length=20)
):
    """
    AI增强择日分析
    
    参数:
    - year, month, day: 日期
    - purpose: 用途
    
    返回: 日期运势 + AI深度建议
    """
    try:
        fortune = get_today_fortune(year, month, day)
        ai_enabled = llm_helper.is_available()
        ai_enhanced = False
        ai_message = "AI服务未配置，已返回基础解读"

        if ai_enabled:
            ai_advice = llm_helper.enhance_zeri_advice(fortune, purpose)
            if ai_advice:
                fortune['ai_advice'] = ai_advice
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/zeri/auspicious")
async def find_auspicious_days_api(
    request: Request,
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    purpose: str = Query("通用", min_length=1, max_length=20),
    days: int = Query(30, ge=1, le=366)
):
    """
    查找吉日
    
    参数:
    - year: 年份
    - month: 月份
    - purpose: 用途（结婚、开业、搬家、出行、动土、安葬、祈福、求财、通用）
    - days: 查找天数（默认30天）
    
    返回: 吉日列表
    """
    try:
        auspicious_days = find_auspicious_days(year, month, purpose, days)
        return success_response(
            {
                "purpose": purpose,
                "total_count": len(auspicious_days),
                "days": auspicious_days
            },
            request=request,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找错误: {str(e)}")


@app.post("/api/ai/chat")
async def ai_chat(
    request: Request,
    question: Optional[str] = Query(None, min_length=1, max_length=500),
    context: Optional[str] = Query(None, max_length=2000),
    payload: Optional[AIChatRequest] = Body(default=None),
):
    """
    AI对话接口
    
    参数:
    - question: 用户问题
    - context: 上下文信息（可选）
    
    返回: AI回复
    """
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
                }
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
                }
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
    except Exception as e:
        mark_ai_failure(f"chat_exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"对话错误: {str(e)}")


@app.post("/api/ai/enhance-bazi")
async def ai_enhance_bazi(payload: BaZiRequest, request: Request):
    """
    AI增强八字分析
    
    参数: 同八字排盘API
    返回: 八字信息 + AI深度分析
    """
    try:
        # 先获取基础八字信息
        datetime(payload.year, payload.month, payload.day, payload.hour, payload.minute)
        
        chart = BaZiChart(
            payload.year,
            payload.month,
            payload.day,
            payload.hour,
            payload.minute,
            payload.gender
        )
        
        result = chart.to_dict()
        result['analysis'] = generate_simple_analysis(chart)
        result['advanced_analysis'] = get_advanced_analysis(chart)
        ai_enabled = llm_helper.is_available()
        ai_enhanced = False
        ai_message = "AI服务未配置，已返回基础解读"

        if ai_enabled:
            ai_analysis = llm_helper.enhance_bazi_analysis(result)
            if ai_analysis:
                result['ai_analysis'] = ai_analysis
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
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/ai/status")
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
            "last_error_at": AI_RUNTIME_STATE["last_error_at"]
        },
        request=request,
    )


def generate_simple_analysis(chart: BaZiChart) -> dict:
    """生成简单的命理分析"""
    wuxing_count = chart.get_wuxing_count()
    
    # 找出最强和最弱的五行
    max_wuxing = max(wuxing_count, key=wuxing_count.get)
    min_wuxing = min(wuxing_count, key=wuxing_count.get)
    
    # 五行建议
    wuxing_advice = {
        '木': {
            'strong': '木旺，性格直爽，适合从事创造性工作。注意肝胆健康。',
            'weak': '木弱，需要补木。适合多接触绿色，从事文化教育行业。'
        },
        '火': {
            'strong': '火旺，热情积极，适合从事社交、表演类工作。注意心血管健康。',
            'weak': '火弱，需要补火。适合多接触红色，从事热情洋溢的行业。'
        },
        '土': {
            'strong': '土旺，稳重踏实，适合从事管理、房地产工作。注意脾胃健康。',
            'weak': '土弱，需要补土。适合多接触黄色，从事稳定的行业。'
        },
        '金': {
            'strong': '金旺，果断坚毅，适合从事金融、技术工作。注意呼吸系统健康。',
            'weak': '金弱，需要补金。适合多接触白色，从事精密技术行业。'
        },
        '水': {
            'strong': '水旺，聪明灵活，适合从事智慧、流动性工作。注意肾脏健康。',
            'weak': '水弱，需要补水。适合多接触黑色，从事智慧型行业。'
        }
    }
    
    analysis = {
        'wuxing_summary': f"五行中{max_wuxing}最旺（{wuxing_count[max_wuxing]:.1f}），{min_wuxing}最弱（{wuxing_count[min_wuxing]:.1f}）",
        'strong_element': {
            'element': max_wuxing,
            'count': wuxing_count[max_wuxing],
            'advice': wuxing_advice[max_wuxing]['strong']
        },
        'weak_element': {
            'element': min_wuxing,
            'count': wuxing_count[min_wuxing],
            'advice': wuxing_advice[min_wuxing]['weak']
        },
        'balance_advice': get_balance_advice(wuxing_count),
        'disclaimer': '以上分析仅供参考，具体情况需要结合完整命盘综合判断。'
    }
    
    return analysis


def get_balance_advice(wuxing_count: dict) -> str:
    """根据五行平衡给出建议"""
    # 计算五行差异
    max_count = max(wuxing_count.values())
    min_count = min(wuxing_count.values())
    diff = max_count - min_count
    
    if diff < 2:
        return "五行较为平衡，命局稳定，发展较为顺利。"
    elif diff < 4:
        return "五行有一定偏颇，建议在生活中注意平衡，补足弱项。"
    else:
        return "五行偏颇较大，建议通过方位、颜色、职业等方式调整平衡。"


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("玄学预测系统API服务启动中...")
    print("访问地址: http://localhost:8002")
    print("API文档: http://localhost:8002/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8002)
