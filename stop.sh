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

# 停止服务
stop_services() {
    # 停止 bot 服务
    if [ -f "bot.pid" ]; then
        BOT_PID=$(cat bot.pid)
        if kill -0 $BOT_PID 2>/dev/null; then
            print_message "Stopping bot service (PID: $BOT_PID)..." "$YELLOW"
            kill $BOT_PID
            rm bot.pid
        fi
    fi
    
    # 停止 web 服务
    if [ -f "web.pid" ]; then
        WEB_PID=$(cat web.pid)
        if kill -0 $WEB_PID 2>/dev/null; then
            print_message "Stopping web service (PID: $WEB_PID)..." "$YELLOW"
            kill $WEB_PID
            rm web.pid
        fi
    fi
    
    print_message "All services stopped successfully!" "$GREEN"
}

# 主函数
main() {
    print_message "Stopping CBots services..." "$YELLOW"
    stop_services
}

# 运行主函数
main 