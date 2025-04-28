#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
精简版MuteBot主程序入口，仅保留禁言和验证功能
"""

# 首先导入补丁模块，修复Python 3.13中imghdr模块缺失的问题
try:
    import tweepy_patch
    print("已加载tweepy补丁，修复imghdr模块")
except Exception as e:
    print(f"加载tweepy补丁失败: {e}")

import logging
import asyncio
import threading
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram_core import TelegramCore
from telegram_api import TelegramAPI
# 修改导入，不再尝试导入WebService类
import web_service
from message_handlers import MessageHandlers
from telethon import events
import signal
import time

# 加载环境变量
load_dotenv()

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

# 全局变量
running = True
telegram_thread = None
telegram_api_thread = None
web_service_thread = None
# 创建一个全局的TelegramCore实例，避免多个实例导致数据库锁定
global_telegram_core = None

class BotService:
    def __init__(self):
        self.telegram_core = TelegramCore()
        self.telegram_api = TelegramAPI(core=self.telegram_core)
        self.message_handlers = None
        self.is_running = False
        self.last_message_time = None
        
    async def start(self):
        """启动服务"""
        try:
            # 启动 Telegram 核心服务
            if not await self.telegram_core.start():
                logger.error("无法启动 Telegram 核心服务")
                return False
                
            # 启动 API 服务
            if not await self.telegram_api.start():
                logger.error("无法启动 Telegram API 服务")
                return False
            
            # 更新状态
            self.is_running = True
            logger.info("服务启动成功")
            return True
        except Exception as e:
            logger.error(f"启动服务时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    async def stop(self):
        """停止服务"""
        try:
            if self.telegram_core.client:
                await self.telegram_core.client.disconnect()
            self.is_running = False
            logger.info("服务已停止")
            return True
        except Exception as e:
            logger.error(f"停止服务时出错: {e}", exc_info=True)
            return False
            
    async def send_reminder_message(self):
        """每隔3小时发送提醒消息"""
        try:
            if not self.is_running or not self.message_handlers:
                return
                
            # 生成提醒消息
            message = self.message_handlers.generate_random_message()
            
            # 发送消息
            await self.telegram_core.send_message(message)
            
            # 更新最后发送时间
            self.last_message_time = datetime.now()
            
            logger.info("成功发送提醒消息")
            
        except Exception as e:
            logger.error(f"发送提醒消息时出错: {e}", exc_info=True)
            
    async def run(self):
        """运行服务主循环"""
        try:
            while running:
                if not self.is_running:
                    # 尝试重启服务
                    if await self.start():
                        logger.info("服务已成功重启")
                    else:
                        logger.error("无法重启服务")
                        await asyncio.sleep(60)  # 等待1分钟后重试
                        continue
                        
                # 检查是否需要发送提醒消息
                now = datetime.now()
                if (not self.last_message_time or 
                    now - self.last_message_time >= timedelta(hours=3)):
                    await self.send_reminder_message()
                    
                await asyncio.sleep(60)  # 每分钟检查一次
                
        except Exception as e:
            logger.error(f"服务主循环出错: {e}", exc_info=True)
            self.is_running = False
            
def signal_handler(sig, frame):
    """处理程序退出信号"""
    global running
    logger.info("收到退出信号，正在关闭所有服务...")
    running = False
    stop_all_services()
    sys.exit(0)

def start_telegram_service():
    """启动 Telegram 核心服务"""
    global global_telegram_core
    
    try:
        logger.info("正在启动 Telegram 核心服务...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 初始化全局TelegramCore实例
        global_telegram_core = TelegramCore()
        
        async def start():
            await global_telegram_core.start()
            logger.info("Telegram 核心服务启动成功")
            
            # 保持服务运行
            while running:
                await asyncio.sleep(1)
                
            # 关闭服务
            await global_telegram_core.stop()
            
        # 运行核心服务
        loop.run_until_complete(start())
        
    except Exception as e:
        logger.error(f"启动 Telegram 核心服务出错: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())

def start_telegram_api_service():
    """启动 Telegram API 服务"""
    global global_telegram_core
    
    try:
        logger.info("正在启动 Telegram API 服务...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 等待确保全局TelegramCore实例已创建
        while global_telegram_core is None:
            time.sleep(0.5)
            
        # 使用全局TelegramCore实例
        telegram_api = TelegramAPI(core=global_telegram_core)
        
        async def start():
            try:
                # 使用正确的start方法
                await telegram_api.start()
                logger.info("Telegram API 服务启动成功")
                
                # 保持服务运行
                while running:
                    await asyncio.sleep(1)
                    
                # 关闭服务
                await telegram_api.stop()
            except Exception as e:
                logger.error(f"Telegram API服务运行出错: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
        # 运行API服务
        loop.run_until_complete(start())
        
    except Exception as e:
        logger.error(f"启动 Telegram API 服务出错: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())

def start_web_service():
    """启动 Web 服务"""
    try:
        logger.info("正在启动 Web 服务...")
        
        # 获取端口
        MODE = os.getenv('MODE', 'prod').lower()
        if MODE == 'dev':
            PORT = int(os.getenv('DEV_PORT', '8873'))
            logger.info(f"Web服务运行在开发模式，使用端口: {PORT}")
        else:
            PORT = int(os.getenv('PRD_PORT', '8872'))
            logger.info(f"Web服务运行在生产模式，使用端口: {PORT}")
        
        # 运行Flask应用
        import web_service
        from web_service import app
        
        # 启动web服务
        threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True),
            daemon=True
        ).start()
        
        logger.info(f"Web 服务启动成功，可访问: http://localhost:{PORT}/")
        # 测试端口
        import socket
        import time
        time.sleep(2)  # 等待2秒让服务启动
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', PORT))
            if result == 0:
                logger.info(f"确认端口 {PORT} 已成功开启并可访问")
            else:
                logger.error(f"警告: 端口 {PORT} 可能未成功开启，请检查 (错误码: {result})")
            sock.close()
        except Exception as e:
            logger.error(f"测试端口时出错: {e}")
            
    except Exception as e:
        logger.error(f"启动 Web 服务出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

def start_all_services():
    """启动所有服务"""
    global telegram_thread, telegram_api_thread, web_service_thread
    
    # 启动 Telegram 核心服务
    telegram_thread = threading.Thread(target=start_telegram_service, name="TelegramCoreThread")
    telegram_thread.daemon = True
    telegram_thread.start()
    
    # 等待 Telegram 核心服务启动成功
    time.sleep(3)  # 增加等待时间，确保核心服务完全启动
    
    # 启动 Telegram API 服务
    telegram_api_thread = threading.Thread(target=start_telegram_api_service, name="TelegramAPIThread")
    telegram_api_thread.daemon = True
    telegram_api_thread.start()
    
    # 等待 API 启动
    time.sleep(2)  # 增加等待时间
    
    # 启动 Web 服务
    web_service_thread = threading.Thread(target=start_web_service, name="WebServiceThread")
    web_service_thread.daemon = True
    web_service_thread.start()
    
    logger.info("所有服务启动成功")

def stop_all_services():
    """停止所有服务"""
    logger.info("正在停止所有服务...")
    
    # 这里不需要特别停止，因为我们使用的是 daemon 线程
    # 当主线程退出时，所有 daemon 线程会自动结束
    
    logger.info("所有服务已停止")

def main():
    """主函数"""
    try:
        # 设置日志
        setup_logging()
        logger.info("正在启动 MuteBot 服务...")
        
        # 设置信号处理函数
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动所有服务
        start_all_services()
        
        # 保持主线程运行
        while running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在退出...")
        stop_all_services()
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
        stop_all_services()

if __name__ == '__main__':
    main() 