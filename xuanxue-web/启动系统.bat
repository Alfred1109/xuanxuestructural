@echo off
chcp 65001 >nul
title 玄学预测系统 - 启动器

echo ========================================
echo    玄学预测系统 - 快速启动
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python已安装
echo.

:: 检查依赖是否安装
echo [检查] 正在检查依赖...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [!] 依赖未安装，正在安装...
    cd backend
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    cd ..
    echo [✓] 依赖安装完成
) else (
    echo [✓] 依赖已安装
)

echo.
echo ========================================
echo    正在启动后端服务...
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 可以停止服务
echo ========================================
echo.

:: 启动后端服务
cd backend
start "玄学预测系统-后端" python main.py

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 打开前端页面
echo.
echo [✓] 正在打开前端页面...
cd ..
start "" "%CD%\frontend\index.html"

echo.
echo ========================================
echo    系统已启动！
echo ========================================
echo.
echo 前端页面应该已经在浏览器中打开
echo 如果没有自动打开，请手动打开: frontend\index.html
echo.
echo 按任意键退出启动器（后端服务将继续运行）
pause >nul
