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

is_port_in_use() {
    local port="$1"
    if command -v lsof > /dev/null 2>&1; then
        lsof -ti:"$port" >/dev/null 2>&1
        return $?
    fi
    if command -v ss > /dev/null 2>&1; then
        ss -ltn "( sport = :$port )" | tail -n +2 | grep -q .
        return $?
    fi
    return 1
}

wait_for_http() {
    local url="$1"
    local attempts="${2:-20}"
    local delay="${3:-1}"
    local i

    for ((i=1; i<=attempts; i++)); do
        if curl -fsS "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep "$delay"
    done
    return 1
}

show_recent_log() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "---- 最近日志 ($file) ----"
        tail -n 20 "$file"
        echo "-------------------------"
    fi
}

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
if ! "$BACKEND_DIR/venv/bin/python" -c "import fastapi, uvicorn, pydantic" >/dev/null 2>&1; then
    echo "📦 正在安装依赖..."
    cd "$BACKEND_DIR"
    venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo "✓ 依赖安装完成"
    echo ""
fi

if is_port_in_use 8002; then
    echo "❌ 端口 8002 已被占用，无法启动后端服务"
    echo "   请先运行 ./stop.sh 或释放该端口后重试"
    exit 1
fi

if is_port_in_use 8003; then
    echo "❌ 端口 8003 已被占用，无法启动前端服务"
    echo "   请先运行 ./stop.sh 或释放该端口后重试"
    exit 1
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
if wait_for_http "http://localhost:8002/" 20 1; then
    echo "✓ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    show_recent_log /tmp/xuanxue-backend.log
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    rm -f /tmp/xuanxue-backend.pid
    exit 1
fi
echo ""

# 启动MkDocs知识库服务
echo "📚 启动知识库服务..."
cd "$SCRIPT_DIR"
if command -v mkdocs > /dev/null; then
    if is_port_in_use 8004; then
        echo "⚠️  端口 8004 已被占用，跳过知识库服务启动"
        echo "   如需启动知识库，请先释放该端口"
    else
    mkdocs serve -a localhost:8004 > /tmp/xuanxue-mkdocs.log 2>&1 &
    MKDOCS_PID=$!
    echo "✓ 知识库服务已启动 (PID: $MKDOCS_PID)"
    echo "   访问地址: http://localhost:8004"
    echo "   日志文件: /tmp/xuanxue-mkdocs.log"
    echo $MKDOCS_PID > /tmp/xuanxue-mkdocs.pid
    fi
else
    echo "⚠️  未安装MkDocs，知识库服务未启动"
    echo "   安装方法: pip install mkdocs mkdocs-material"
fi
echo ""

# 启动前端HTTP服务器
echo "🌐 启动前端服务器..."
cd "$FRONTEND_DIR"
python3 -m http.server 8003 > /tmp/xuanxue-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ 前端服务器已启动 (PID: $FRONTEND_PID)"
echo "   访问地址: http://localhost:8003"
echo "   日志文件: /tmp/xuanxue-frontend.log"
echo $FRONTEND_PID > /tmp/xuanxue-frontend.pid
echo ""

# 等待前端服务启动
if wait_for_http "http://localhost:8003/index.html" 10 1; then
    echo "✓ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
    show_recent_log /tmp/xuanxue-frontend.log
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    rm -f /tmp/xuanxue-frontend.pid /tmp/xuanxue-backend.pid
    exit 1
fi

# 打开浏览器
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:8003/index.html" 2>/dev/null &
    echo "✓ 前端页面已在浏览器中打开"
elif command -v gnome-open > /dev/null; then
    gnome-open "http://localhost:8003/index.html" 2>/dev/null &
    echo "✓ 前端页面已在浏览器中打开"
else
    echo "⚠️  无法自动打开浏览器"
    echo "   请手动打开: http://localhost:8003/index.html"
fi

echo ""
echo "======================================"
echo "  系统启动完成！"
echo "======================================"
echo ""
echo "📌 使用说明："
echo "   - 前端界面: http://localhost:8003"
echo "   - 后端API: http://localhost:8002"
echo "   - API文档: http://localhost:8002/docs"
if [ -f /tmp/xuanxue-mkdocs.pid ]; then
    echo "   - 知识库: http://localhost:8004"
fi
echo ""
echo "📌 停止服务："
echo "   运行: ./stop.sh"
echo ""
echo "💡 提示："
echo "   - 前端日志: tail -f /tmp/xuanxue-frontend.log"
echo "   - 后端日志: tail -f /tmp/xuanxue-backend.log"
if [ -f /tmp/xuanxue-mkdocs.pid ]; then
    echo "   - 知识库日志: tail -f /tmp/xuanxue-mkdocs.log"
fi
if [ -z "$ARK_API_KEY" ]; then
    echo "   - AI功能: 未启用，设置方法见 AI配置指南.md"
else
    echo "   - AI功能: 已启用 ✓"
fi
echo ""

# 保存PID到文件，方便停止
echo $BACKEND_PID > /tmp/xuanxue-backend.pid
