"""
玄学预测系统 - FastAPI后端主程序
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class BaZiRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    gender: str = "男"


class CalendarRequest(BaseModel):
    year: int
    month: int
    day: int


@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "欢迎使用玄学预测系统API",
        "version": "1.0.0",
        "endpoints": {
            "八字排盘": "/api/bazi",
            "阳历转农历": "/api/calendar/solar-to-lunar",
            "农历转阳历": "/api/calendar/lunar-to-solar",
            "年份干支": "/api/ganzhi/year"
        }
    }


@app.post("/api/bazi")
async def calculate_bazi(request: BaZiRequest):
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
        datetime(request.year, request.month, request.day, request.hour, request.minute)
        
        # 创建八字命盘
        chart = BaZiChart(
            request.year,
            request.month,
            request.day,
            request.hour,
            request.minute,
            request.gender
        )
        
        # 返回完整信息
        result = chart.to_dict()
        
        # 添加基础分析
        result['analysis'] = generate_simple_analysis(chart)
        
        # 添加高级分析
        result['advanced_analysis'] = get_advanced_analysis(chart)
        
        return {
            "success": True,
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.post("/api/divination/liuyao")
async def liuyao_divination(question: str = ""):
    """
    六爻占卜API
    
    参数:
    - question: 占卜的问题（可选）
    
    返回: 卦象和解释
    """
    try:
        result = divine(question)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.post("/api/ai/enhance-liuyao")
async def ai_enhance_liuyao(question: str = ""):
    """
    AI增强六爻占卜
    
    参数:
    - question: 占卜的问题（可选）
    
    返回: 卦象 + AI深度解读
    """
    try:
        result = divine(question)
        
        # AI增强解读
        if llm_helper.is_available():
            ai_interpretation = llm_helper.enhance_liuyao_interpretation(result)
            if ai_interpretation:
                result['ai_interpretation'] = ai_interpretation
        
        return {
            "success": True,
            "data": result,
            "ai_enabled": llm_helper.is_available()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.post("/api/divination/qimen")
async def qimen_divination(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    matter_type: str = "通用"
):
    """
    奇门遁甲占卜API
    
    参数:
    - year, month, day, hour, minute: 时间
    - matter_type: 事项类型（求财、求职、婚姻、出行、诉讼、疾病、学业、通用）
    
    返回: 奇门遁甲盘和分析
    """
    try:
        result = divine_qimen(year, month, day, hour, minute, matter_type)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.get("/api/divination/qimen/current")
async def get_current_qimen_api(matter_type: str = "通用"):
    """
    获取当前时刻的奇门遁甲盘
    
    参数:
    - matter_type: 事项类型（求财、求职、婚姻、出行、诉讼、疾病、学业、通用）
    
    返回: 当前时刻的奇门遁甲盘和分析
    """
    try:
        result = get_current_qimen(matter_type)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.post("/api/ai/enhance-qimen")
async def ai_enhance_qimen(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    matter_type: str = "通用"
):
    """
    AI增强奇门遁甲占卜
    
    参数:
    - year, month, day, hour, minute: 时间
    - matter_type: 事项类型
    
    返回: 奇门遁甲盘 + AI深度解读
    """
    try:
        result = divine_qimen(year, month, day, hour, minute, matter_type)
        
        # AI增强解读
        if llm_helper.is_available():
            ai_interpretation = llm_helper.enhance_qimen_interpretation(result, matter_type)
            if ai_interpretation:
                result['ai_interpretation'] = ai_interpretation
        
        return {
            "success": True,
            "data": result,
            "ai_enabled": llm_helper.is_available()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"占卜错误: {str(e)}")


@app.post("/api/calendar/solar-to-lunar")
async def convert_solar_to_lunar(request: CalendarRequest):
    """阳历转农历"""
    try:
        lunar = solar_to_lunar(request.year, request.month, request.day)
        return {
            "success": True,
            "data": {
                "solar": {
                    "year": request.year,
                    "month": request.month,
                    "day": request.day
                },
                "lunar": {
                    "year": lunar[0],
                    "month": lunar[1],
                    "day": lunar[2],
                    "is_leap": lunar[3]
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换错误: {str(e)}")


@app.get("/api/ganzhi/year/{year}")
async def get_year_ganzhi_api(year: int):
    """获取年份干支"""
    try:
        ganzhi = get_year_ganzhi(year)
        return {
            "success": True,
            "data": {
                "year": year,
                "ganzhi": ganzhi
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/zeri/today")
async def get_today_fortune_api():
    """获取今日运势"""
    try:
        today = datetime.now()
        fortune = get_today_fortune(today.year, today.month, today.day)
        return {
            "success": True,
            "data": fortune
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/zeri/date/{year}/{month}/{day}")
async def get_date_fortune_api(year: int, month: int, day: int):
    """获取指定日期运势"""
    try:
        fortune = get_today_fortune(year, month, day)
        return {
            "success": True,
            "data": fortune
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/ai/enhance-zeri/{year}/{month}/{day}")
async def ai_enhance_zeri(year: int, month: int, day: int, purpose: str = "通用"):
    """
    AI增强择日分析
    
    参数:
    - year, month, day: 日期
    - purpose: 用途
    
    返回: 日期运势 + AI深度建议
    """
    try:
        fortune = get_today_fortune(year, month, day)
        
        # AI增强建议
        if llm_helper.is_available():
            ai_advice = llm_helper.enhance_zeri_advice(fortune, purpose)
            if ai_advice:
                fortune['ai_advice'] = ai_advice
        
        return {
            "success": True,
            "data": fortune,
            "ai_enabled": llm_helper.is_available()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/zeri/auspicious")
async def find_auspicious_days_api(
    year: int,
    month: int,
    purpose: str = "通用",
    days: int = 30
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
        return {
            "success": True,
            "data": {
                "purpose": purpose,
                "total_count": len(auspicious_days),
                "days": auspicious_days
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查找错误: {str(e)}")


@app.post("/api/ai/chat")
async def ai_chat(question: str, context: str = ""):
    """
    AI对话接口
    
    参数:
    - question: 用户问题
    - context: 上下文信息（可选）
    
    返回: AI回复
    """
    try:
        if not llm_helper.is_available():
            return {
                "success": False,
                "message": "AI服务未配置，请设置ARK_API_KEY环境变量"
            }
        
        response = llm_helper.chat(question, context if context else None)
        
        if response:
            return {
                "success": True,
                "data": {
                    "question": question,
                    "answer": response
                }
            }
        else:
            return {
                "success": False,
                "message": "AI服务暂时不可用"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话错误: {str(e)}")


@app.post("/api/ai/enhance-bazi")
async def ai_enhance_bazi(request: BaZiRequest):
    """
    AI增强八字分析
    
    参数: 同八字排盘API
    返回: 八字信息 + AI深度分析
    """
    try:
        # 先获取基础八字信息
        datetime(request.year, request.month, request.day, request.hour, request.minute)
        
        chart = BaZiChart(
            request.year,
            request.month,
            request.day,
            request.hour,
            request.minute,
            request.gender
        )
        
        result = chart.to_dict()
        result['analysis'] = generate_simple_analysis(chart)
        result['advanced_analysis'] = get_advanced_analysis(chart)
        
        # AI增强分析
        if llm_helper.is_available():
            ai_analysis = llm_helper.enhance_bazi_analysis(result)
            if ai_analysis:
                result['ai_analysis'] = ai_analysis
        
        return {
            "success": True,
            "data": result,
            "ai_enabled": llm_helper.is_available()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")


@app.get("/api/ai/status")
async def ai_status():
    """检查AI服务状态"""
    return {
        "success": True,
        "data": {
            "available": llm_helper.is_available(),
            "model": llm_helper.model if llm_helper.is_available() else None,
            "message": "AI服务正常" if llm_helper.is_available() else "AI服务未配置"
        }
    }


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
