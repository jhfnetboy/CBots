#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 检查 Python 环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_message "Error: Python3 is not installed" "$RED"
        exit 1
    fi
}

# 检查虚拟环境
check_venv() {
    if [ ! -d "venv" ]; then
        print_message "Creating virtual environment..." "$YELLOW"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
}

# 启动服务
start_services() {
    # 启动 bot 服务
    print_message "Starting bot service..." "$YELLOW"
    cd bot
    python main.py &
    BOT_PID=$!
    cd ..
    
    # 等待 bot 服务启动
    sleep 2
    
    # 启动 web 服务
    print_message "Starting web service..." "$YELLOW"
    cd web
    python web.py &
    WEB_PID=$!
    cd ..
    
    # 保存进程 ID
    echo $BOT_PID > bot.pid
    echo $WEB_PID > web.pid
    
    print_message "Services started successfully!" "$GREEN"
    print_message "Bot service PID: $BOT_PID" "$GREEN"
    print_message "Web service PID: $WEB_PID" "$GREEN"
    print_message "To stop services, run: ./stop.sh" "$YELLOW"
}

# 主函数
main() {
    print_message "Starting CBots services..." "$YELLOW"
    
    # 检查 Python 环境
    check_python
    
    # 检查并激活虚拟环境
    check_venv
    
    # 启动服务
    start_services
}

# 运行主函数
main 