#!/bin/bash

# 玄学预测系统 - 一键启动脚本

echo "======================================"
echo "  玄学预测系统 - 启动中..."
echo "======================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/xuanxue-web/backend"
FRONTEND_DIR="$SCRIPT_DIR/xuanxue-web/frontend"

# 加载环境变量
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc" 2>/dev/null || true
fi

# 检查AI配置
if [ -n "$ARK_API_KEY" ]; then
    echo "✓ 检测到AI配置 (ARK_API_KEY)"
    AI_STATUS="已启用"
else
    echo "⚠️  未检测到AI配置"
    echo "   如需AI功能，请设置: export ARK_API_KEY=your_key"
    AI_STATUS="未配置"
fi
echo ""

# 检查虚拟环境是否存在
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    cd "$BACKEND_DIR"
    python3 -m venv venv
    echo "✓ 虚拟环境创建完成"
    echo ""
fi

# 检查依赖是否安装
if [ ! -f "$BACKEND_DIR/venv/lib/python3.12/site-packages/fastapi/__init__.py" ]; then
    echo "📦 正在安装依赖..."
    cd "$BACKEND_DIR"
    venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo "✓ 依赖安装完成"
    echo ""
fi

# 启动后端服务器（后台运行）
echo "🚀 启动后端服务器..."
cd "$BACKEND_DIR"
# 传递环境变量给后端进程
if [ -n "$ARK_API_KEY" ]; then
    ARK_API_KEY="$ARK_API_KEY" venv/bin/python main.py > /tmp/xuanxue-backend.log 2>&1 &
else
    venv/bin/python main.py > /tmp/xuanxue-backend.log 2>&1 &
fi
BACKEND_PID=$!
echo "✓ 后端服务器已启动 (PID: $BACKEND_PID)"
echo "   访问地址: http://localhost:8002"
echo "   API文档: http://localhost:8002/docs"
echo "   日志文件: /tmp/xuanxue-backend.log"
echo "   AI状态: $AI_STATUS"
echo ""

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 检查后端是否成功启动
if curl -s http://localhost:8002/ > /dev/null 2>&1; then
    echo "✓ 后端服务启动成功"
else
    echo "⚠️  后端服务可能未完全启动，请稍等片刻"
fi
echo ""

# 打开前端页面
echo "🌐 打开前端页面..."
FRONTEND_INDEX="$FRONTEND_DIR/index.html"

if [ -f "$FRONTEND_INDEX" ]; then
    # 尝试使用默认浏览器打开
    if command -v xdg-open > /dev/null; then
        xdg-open "$FRONTEND_INDEX" 2>/dev/null &
        echo "✓ 前端页面已在浏览器中打开"
    elif command -v gnome-open > /dev/null; then
        gnome-open "$FRONTEND_INDEX" 2>/dev/null &
        echo "✓ 前端页面已在浏览器中打开"
    else
        echo "⚠️  无法自动打开浏览器"
        echo "   请手动打开: file://$FRONTEND_INDEX"
    fi
else
    echo "❌ 前端文件不存在: $FRONTEND_INDEX"
fi

echo ""
echo "======================================"
echo "  系统启动完成！"
echo "======================================"
echo ""
echo "📌 使用说明："
echo "   - 前端界面: file://$FRONTEND_INDEX"
echo "   - 后端API: http://localhost:8002"
echo "   - API文档: http://localhost:8002/docs"
echo ""
echo "📌 停止服务："
echo "   kill $BACKEND_PID"
echo "   或运行: ./stop.sh"
echo ""
echo "💡 提示："
echo "   - 后端日志: tail -f /tmp/xuanxue-backend.log"
if [ -z "$ARK_API_KEY" ]; then
    echo "   - AI功能: 未启用，设置方法见 AI配置指南.md"
else
    echo "   - AI功能: 已启用 ✓"
fi
echo ""

# 保存PID到文件，方便停止
echo $BACKEND_PID > /tmp/xuanxue-backend.pid
