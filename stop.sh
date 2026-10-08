#!/bin/bash

# 玄学预测系统 - 停止脚本

set -u

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/xuanxue-web/backend"
FRONTEND_DIR="$SCRIPT_DIR/xuanxue-web/frontend"
BACKEND_PORT=8002
FRONTEND_MODE="${FRONTEND_MODE:-nginx}"
FRONTEND_PORT="${FRONTEND_PORT:-8003}"
BACKEND_PID_FILE=/tmp/xuanxue-backend.pid
FRONTEND_PID_FILE=/tmp/xuanxue-frontend.pid

echo "======================================"
echo "  玄学预测系统 - 停止服务..."
echo "======================================"
echo ""

list_port_pids() {
    local port="$1"
    if command -v lsof > /dev/null 2>&1; then
        lsof -t -sTCP:LISTEN -iTCP:"$port" 2>/dev/null
        return 0
    fi
    if command -v ss > /dev/null 2>&1; then
        ss -ltnp "( sport = :$port )" 2>/dev/null | awk -F'pid=' 'NF>1 {split($2, a, ","); print a[1]}' | sort -u
        return 0
    fi
    return 1
}

stop_pid_if_running() {
    local pid="$1"
    local name="$2"
    local expected_dir="$3"
    if [ -z "$pid" ]; then
        return 0
    fi
    if ps -p "$pid" > /dev/null 2>&1; then
        if [ "$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)" != "$expected_dir" ]; then
            echo "❌ PID $pid 不属于本项目，拒绝停止。请检查PID文件与端口归属。"
            return 1
        fi
        echo "🛑 停止$name (PID: $pid)..."
        kill "$pid" >/dev/null 2>&1 || true
        sleep 1
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "⚠️  进程未响应，强制停止..."
            kill -9 "$pid" >/dev/null 2>&1 || true
        fi
        echo "✓ $name已停止"
    else
        echo "⚠️  $name未运行 (PID: $pid)"
    fi
}

# 停止后端服务
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    stop_pid_if_running "$BACKEND_PID" "后端服务" "$BACKEND_DIR" || exit 1
    rm -f "$BACKEND_PID_FILE"
else
    echo "⚠️  未找到后端PID文件，尝试查找进程..."
    PIDS=$(list_port_pids "$BACKEND_PORT")
    if [ -n "$PIDS" ]; then
        echo "🛑 找到占用$BACKEND_PORT端口的进程: $PIDS"
        for pid in $PIDS; do
            stop_pid_if_running "$pid" "后端服务" "$BACKEND_DIR" || exit 1
        done
        sleep 1
        echo "✓ 后端进程已停止"
    else
        echo "✓ 没有找到运行中的后端服务"
    fi
fi

if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    stop_pid_if_running "$FRONTEND_PID" "前端服务" "$FRONTEND_DIR" || exit 1
    rm -f "$FRONTEND_PID_FILE"
else
    PIDS=""
    if [ "$FRONTEND_MODE" = "local" ]; then
        PIDS=$(list_port_pids "$FRONTEND_PORT")
    fi
    if [ -n "$PIDS" ]; then
        echo "🛑 找到占用$FRONTEND_PORT端口的进程: $PIDS"
        for pid in $PIDS; do
            stop_pid_if_running "$pid" "前端服务" "$FRONTEND_DIR" || exit 1
        done
        sleep 1
        echo "✓ 前端进程已停止"
    else
        if [ "$FRONTEND_MODE" = "local" ]; then
            echo "✓ 没有找到运行中的前端服务"
        else
            echo "ℹ️  当前为 Nginx 统一出口模式，未检测到本地前端静态服务"
        fi
    fi
fi

echo ""
echo "======================================"
echo "  服务已停止"
echo "======================================"
