#!/bin/bash

# 玄学预测系统 - 停止脚本

set -u

BACKEND_PORT=8002
FRONTEND_PORT=8003
BACKEND_PID_FILE=/tmp/xuanxue-backend.pid
FRONTEND_PID_FILE=/tmp/xuanxue-frontend.pid

echo "======================================"
echo "  玄学预测系统 - 停止服务..."
echo "======================================"
echo ""

list_port_pids() {
    local port="$1"
    if command -v lsof > /dev/null 2>&1; then
        lsof -ti:"$port" 2>/dev/null
        return 0
    fi
    return 1
}

stop_pid_if_running() {
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
    stop_pid_if_running "$BACKEND_PID" "后端服务"
    rm -f "$BACKEND_PID_FILE"
else
    echo "⚠️  未找到后端PID文件，尝试查找进程..."
    PIDS=$(list_port_pids "$BACKEND_PORT")
    if [ -n "$PIDS" ]; then
        echo "🛑 找到占用$BACKEND_PORT端口的进程: $PIDS"
        kill $PIDS >/dev/null 2>&1 || true
        sleep 1
        echo "✓ 后端进程已停止"
    else
        echo "✓ 没有找到运行中的后端服务"
    fi
fi

# 停止前端服务
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    stop_pid_if_running "$FRONTEND_PID" "前端服务"
    rm -f "$FRONTEND_PID_FILE"
else
    echo "⚠️  未找到前端PID文件，尝试查找进程..."
    PIDS=$(list_port_pids "$FRONTEND_PORT")
    if [ -n "$PIDS" ]; then
        echo "🛑 找到占用$FRONTEND_PORT端口的进程: $PIDS"
        kill $PIDS >/dev/null 2>&1 || true
        sleep 1
        echo "✓ 前端进程已停止"
    else
        echo "✓ 没有找到运行中的前端服务"
    fi
fi

echo ""
echo "======================================"
echo "  服务已停止"
echo "======================================"
