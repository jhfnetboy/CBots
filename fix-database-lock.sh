#!/bin/bash

# 停止服务
echo "===== 修复数据库锁定问题 ====="
echo "停止所有服务..."
./stop-service.sh

# 检查是否有Python进程在运行
echo "检查是否有Python进程在运行..."
pids=$(ps aux | grep -v grep | grep python | grep main.py | awk '{print $2}')
if [ -n "$pids" ]; then
    echo "发现服务进程，将其终止: $pids"
    kill -9 $pids
    sleep 1
fi

# 清理session文件
echo "清理session文件..."
find . -name "telegram_core_session*" -delete
find ./sessions -name "telegram_session_*" -delete
mkdir -p sessions

echo "数据库锁定问题已修复"

# 启动服务
echo "重新启动服务..."
./reload-service.sh 