#!/bin/bash

# 玄学预测系统 - 停止脚本

echo "======================================"
echo "  玄学预测系统 - 停止服务..."
echo "======================================"
echo ""

# 从PID文件读取进程ID
if [ -f /tmp/xuanxue-backend.pid ]; then
    BACKEND_PID=$(cat /tmp/xuanxue-backend.pid)
    
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "🛑 停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 1
        
        # 检查是否成功停止
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo "⚠️  进程未响应，强制停止..."
            kill -9 $BACKEND_PID
        fi
        
        echo "✓ 后端服务已停止"
    else
        echo "⚠️  后端服务未运行 (PID: $BACKEND_PID)"
    fi
    
    rm -f /tmp/xuanxue-backend.pid
else
    echo "⚠️  未找到PID文件，尝试查找进程..."
    
    # 尝试通过端口查找进程
    PIDS=$(lsof -ti:8002 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        echo "🛑 找到占用8002端口的进程: $PIDS"
        kill $PIDS
        sleep 1
        echo "✓ 进程已停止"
    else
        echo "✓ 没有找到运行中的后端服务"
    fi
fi

echo ""
echo "======================================"
echo "  服务已停止"
echo "======================================"
