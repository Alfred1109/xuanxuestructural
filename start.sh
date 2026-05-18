#!/bin/bash

# 玄学预测系统 - 一键启动脚本

set -u

echo "======================================"
echo "  玄学预测系统 - 启动中..."
echo "======================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/xuanxue-web/backend"
FRONTEND_DIR="$SCRIPT_DIR/xuanxue-web/frontend"
BACKEND_PORT=8002
FRONTEND_PORT=8003
BACKEND_LOG=/tmp/xuanxue-backend.log
FRONTEND_LOG=/tmp/xuanxue-frontend.log
BACKEND_PID_FILE=/tmp/xuanxue-backend.pid
FRONTEND_PID_FILE=/tmp/xuanxue-frontend.pid

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

list_port_pids() {
    local port="$1"
    if command -v lsof > /dev/null 2>&1; then
        lsof -ti:"$port" 2>/dev/null
        return 0
    fi
    if command -v ss > /dev/null 2>&1; then
        ss -ltnp "( sport = :$port )" 2>/dev/null | awk -F'pid=' 'NF>1 {split($2, a, ","); print a[1]}' | sort -u
        return 0
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

wait_for_port_release() {
    local port="$1"
    local attempts="${2:-20}"
    local delay="${3:-1}"
    local i

    for ((i=1; i<=attempts; i++)); do
        if ! is_port_in_use "$port"; then
            return 0
        fi
        sleep "$delay"
    done
    return 1
}

ensure_process_stopped() {
    local pid="$1"
    local name="$2"
    if [ -z "$pid" ]; then
        return 0
    fi
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "🛑 停止$name (PID: $pid)..."
        kill "$pid" >/dev/null 2>&1 || true
        sleep 1
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "⚠️  $name未及时退出，强制停止..."
            kill -9 "$pid" >/dev/null 2>&1 || true
        fi
    fi
}

cleanup_existing_services() {
    echo "🧹 检查旧服务实例..."

    if [ -f "$BACKEND_PID_FILE" ]; then
        ensure_process_stopped "$(cat "$BACKEND_PID_FILE" 2>/dev/null || true)" "后端服务"
        rm -f "$BACKEND_PID_FILE"
    fi
    if [ -f "$FRONTEND_PID_FILE" ]; then
        ensure_process_stopped "$(cat "$FRONTEND_PID_FILE" 2>/dev/null || true)" "前端服务"
        rm -f "$FRONTEND_PID_FILE"
    fi

    if is_port_in_use "$BACKEND_PORT"; then
        local backend_pids
        backend_pids="$(list_port_pids "$BACKEND_PORT" | tr '\n' ' ')"
        if [ -n "$backend_pids" ]; then
            echo "🛑 发现占用 $BACKEND_PORT 的旧进程: $backend_pids"
            kill $backend_pids >/dev/null 2>&1 || true
        fi
    fi
    if is_port_in_use "$FRONTEND_PORT"; then
        local frontend_pids
        frontend_pids="$(list_port_pids "$FRONTEND_PORT" | tr '\n' ' ')"
        if [ -n "$frontend_pids" ]; then
            echo "🛑 发现占用 $FRONTEND_PORT 的旧进程: $frontend_pids"
            kill $frontend_pids >/dev/null 2>&1 || true
        fi
    fi

    wait_for_port_release "$BACKEND_PORT" 20 1 || {
        echo "❌ 端口 $BACKEND_PORT 未能释放"
        exit 1
    }
    wait_for_port_release "$FRONTEND_PORT" 20 1 || {
        echo "❌ 端口 $FRONTEND_PORT 未能释放"
        exit 1
    }
    echo "✓ 旧服务清理完成"
    echo ""
}

# 加载环境变量
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc" 2>/dev/null || true
fi

# 检查AI配置
if [ -n "${ARK_API_KEY:-}" ]; then
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
    echo "📦 虚拟环境不存在，正在创建..."
    cd "$BACKEND_DIR"
    python3 -m venv venv || {
        echo "❌ 虚拟环境创建失败，请先安装 python3-venv / python3.12-venv"
        exit 1
    }
    echo "✓ 虚拟环境创建完成"
    echo ""
fi

# 检查依赖是否安装
if ! "$BACKEND_DIR/venv/bin/python" -c "import fastapi, uvicorn, pydantic, httpx, openai, iztro_py" >/dev/null 2>&1; then
    echo "📦 正在安装依赖..."
    cd "$BACKEND_DIR"
    venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple || {
        echo "❌ 依赖安装失败"
        exit 1
    }
    echo "✓ 依赖安装完成"
    echo ""
fi

cleanup_existing_services

# 启动后端服务器（后台运行）
echo "🚀 启动后端服务器..."
cd "$BACKEND_DIR"
rm -f "$BACKEND_LOG"
# 传递环境变量给后端进程
if [ -n "${ARK_API_KEY:-}" ]; then
    setsid env ARK_API_KEY="$ARK_API_KEY" venv/bin/python main.py > "$BACKEND_LOG" 2>&1 < /dev/null &
else
    setsid venv/bin/python main.py > "$BACKEND_LOG" 2>&1 < /dev/null &
fi
BACKEND_PID=$!
disown || true
echo "✓ 后端服务器已启动 (PID: $BACKEND_PID)"
echo "   访问地址: http://localhost:$BACKEND_PORT"
echo "   API文档: http://localhost:$BACKEND_PORT/docs"
echo "   日志文件: $BACKEND_LOG"
echo "   AI状态: $AI_STATUS"
echo ""
echo "$BACKEND_PID" > "$BACKEND_PID_FILE"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
if wait_for_http "http://localhost:$BACKEND_PORT/" 20 1; then
    echo "✓ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    show_recent_log "$BACKEND_LOG"
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    rm -f "$BACKEND_PID_FILE"
    exit 1
fi
echo ""

echo "🔎 校验关键接口..."
AUTH_ROUTE_STATUS="$(
    curl -s -o /tmp/xuanxue-auth-route-check.json -w "%{http_code}" \
        -X POST "http://localhost:$BACKEND_PORT/api/auth/register" \
        -H "Content-Type: application/json" \
        -d '{}'
)"
if [ "$AUTH_ROUTE_STATUS" != "422" ]; then
    echo "❌ /api/auth/register 校验失败，当前后端可能不是最新版本"
    echo "   返回状态码: $AUTH_ROUTE_STATUS"
    if [ -f /tmp/xuanxue-auth-route-check.json ]; then
        cat /tmp/xuanxue-auth-route-check.json
        echo ""
    fi
    show_recent_log "$BACKEND_LOG"
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    rm -f "$BACKEND_PID_FILE"
    exit 1
fi
echo "✓ 关键接口已就绪"
echo ""

# 启动前端HTTP服务器
echo "🌐 启动前端服务器..."
cd "$FRONTEND_DIR"
rm -f "$FRONTEND_LOG"
setsid python3 -m http.server "$FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 < /dev/null &
FRONTEND_PID=$!
disown || true
echo "✓ 前端服务器已启动 (PID: $FRONTEND_PID)"
echo "   访问地址: http://localhost:$FRONTEND_PORT"
echo "   日志文件: $FRONTEND_LOG"
echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
echo ""

# 等待前端服务启动
if wait_for_http "http://localhost:$FRONTEND_PORT/index.html" 10 1; then
    echo "✓ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
    show_recent_log "$FRONTEND_LOG"
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    rm -f "$FRONTEND_PID_FILE" "$BACKEND_PID_FILE"
    exit 1
fi

# 打开浏览器
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:$FRONTEND_PORT/index.html" 2>/dev/null &
    echo "✓ 前端页面已在浏览器中打开"
elif command -v gnome-open > /dev/null; then
    gnome-open "http://localhost:$FRONTEND_PORT/index.html" 2>/dev/null &
    echo "✓ 前端页面已在浏览器中打开"
else
    echo "⚠️  无法自动打开浏览器"
    echo "   请手动打开: http://localhost:$FRONTEND_PORT/index.html"
fi

echo ""
echo "======================================"
echo "  系统启动完成！"
echo "======================================"
echo ""
echo "📌 使用说明："
echo "   - 前端界面: http://localhost:$FRONTEND_PORT"
echo "   - 后端API: http://localhost:$BACKEND_PORT"
echo "   - API文档: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "📌 停止服务："
echo "   运行: ./stop.sh"
echo ""
echo "💡 提示："
echo "   - 前端日志: tail -f $FRONTEND_LOG"
echo "   - 后端日志: tail -f $BACKEND_LOG"
if [ -z "${ARK_API_KEY:-}" ]; then
    echo "   - AI功能: 未启用，设置方法见 AI配置指南.md"
else
    echo "   - AI功能: 已启用 ✓"
fi
echo ""
