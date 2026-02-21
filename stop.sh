#!/bin/bash

# 玄学预测系统 - 停止脚本

echo "======================================"
echo "  玄学预测系统 - 停止服务..."
echo "======================================"
echo ""

# 停止后端服务
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
    echo "⚠️  未找到后端PID文件，尝试查找进程..."
    
    # 尝试通过端口查找进程
    PIDS=$(lsof -ti:8002 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        echo "🛑 找到占用8002端口的进程: $PIDS"
        kill $PIDS
        sleep 1
        echo "✓ 后端进程已停止"
    else
        echo "✓ 没有找到运行中的后端服务"
    fi
fi

# 停止前端服务
if [ -f /tmp/xuanxue-frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/xuanxue-frontend.pid)
    
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "🛑 停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 1
        
        # 检查是否成功停止
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo "⚠️  进程未响应，强制停止..."
            kill -9 $FRONTEND_PID
        fi
        
        echo "✓ 前端服务已停止"
    else
        echo "⚠️  前端服务未运行 (PID: $FRONTEND_PID)"
    fi
    
    rm -f /tmp/xuanxue-frontend.pid
else
    echo "⚠️  未找到前端PID文件，尝试查找进程..."
    
    # 尝试通过端口查找进程
    PIDS=$(lsof -ti:8003 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        echo "🛑 找到占用8003端口的进程: $PIDS"
        kill $PIDS
        sleep 1
        echo "✓ 前端进程已停止"
    else
        echo "✓ 没有找到运行中的前端服务"
    fi
fi

# 停止MkDocs知识库服务
if [ -f /tmp/xuanxue-mkdocs.pid ]; then
    MKDOCS_PID=$(cat /tmp/xuanxue-mkdocs.pid)
    
    if ps -p $MKDOCS_PID > /dev/null 2>&1; then
        echo "🛑 停止知识库服务 (PID: $MKDOCS_PID)..."
        kill $MKDOCS_PID
        sleep 1
        
        # 检查是否成功停止
        if ps -p $MKDOCS_PID > /dev/null 2>&1; then
            echo "⚠️  进程未响应，强制停止..."
            kill -9 $MKDOCS_PID
        fi
        
        echo "✓ 知识库服务已停止"
    else
        echo "⚠️  知识库服务未运行 (PID: $MKDOCS_PID)"
    fi
    
    rm -f /tmp/xuanxue-mkdocs.pid
else
    # 尝试通过端口查找进程
    PIDS=$(lsof -ti:8004 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        echo "🛑 找到占用8004端口的进程: $PIDS"
        kill $PIDS
        sleep 1
        echo "✓ 知识库进程已停止"
    fi
fi

echo ""
echo "======================================"
echo "  服务已停止"
echo "======================================"
