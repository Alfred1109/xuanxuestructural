"""
玄学预测系统 - FastAPI后端主程序
"""

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError

from api.ai import router as ai_router
from api.auth import router as auth_router
from api.bazi import router as bazi_router
from api.common import (
    AI_RUNTIME_STATE,
    configure_cors,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from api.divination import router as divination_router
from api.fengshui import router as fengshui_router
from api.location import router as location_router
from api.system import router as system_router
from api.ziwei import router as ziwei_router
from core.llm_helper import llm_helper


app = FastAPI(
    title="玄学预测系统API",
    description="综合性玄学预测平台API",
    version="1.0.0",
)


configure_cors(app)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(bazi_router)
app.include_router(ziwei_router)
app.include_router(fengshui_router)
app.include_router(location_router)
app.include_router(divination_router)
app.include_router(ai_router)


if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("玄学预测系统API服务启动中...")
    print("访问地址: http://localhost:8002")
    print("API文档: http://localhost:8002/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8002)
