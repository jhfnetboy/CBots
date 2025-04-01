import logging
import asyncio
import threading
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram_core import TelegramCore
from telegram_api import TelegramAPI
from twitter_core import TwitterCore
from twitter_api import TwitterAPI
from web_service import WebService
from message_handlers import MessageHandlers
from telethon import events

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

class BotService:
    def __init__(self):
        self.telegram_core = TelegramCore()
        self.telegram_api = TelegramAPI(core=self.telegram_core)
        self.twitter_core = TwitterCore()
        self.twitter_api = TwitterAPI(core=self.twitter_core)
        self.message_handlers = None
        self.is_running = False
        self.last_message_time = None
        
    async def start(self):
        """Start the application"""
        try:
            # 启动 Telegram 核心服务
            if not await self.telegram_core.start():
                print("Failed to start Telegram core service")
                return False
                
            # 启动 Twitter 核心服务 (可选)
            if self.twitter_core:
                if not await self.twitter_core.start():
                    print("Failed to start Twitter core service")
                    # Twitter 服务失败不影响整体运行
                    print("Continuing without Twitter service")
            
            # 启动 API 服务
            if not await self.telegram_api.start():
                print("Failed to start Telegram API service")
                return False
                
            if self.twitter_api:
                if not await self.twitter_api.start():
                    print("Failed to start Twitter API service")
                    # Twitter API 服务失败不影响整体运行
                    print("Continuing without Twitter API service")
            
            # 更新状态
            self.is_running = True
            print("Application started successfully")
            return True
        except Exception as e:
            print(f"Error starting application: {e}")
            import traceback
            print(traceback.format_exc())
            return False
            
    async def stop(self):
        """停止服务"""
        try:
            if self.telegram_core.client:
                await self.telegram_core.client.disconnect()
            self.is_running = False
            logger.info("Bot service stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping bot service: {e}", exc_info=True)
            return False
            
    async def send_random_message(self):
        """发送随机消息"""
        try:
            if not self.is_running:
                return
                
            # 生成随机消息
            message = self.message_handlers.generate_random_message()
            
            # 发送消息
            await self.telegram_core.send_message(message)
            
            # 更新最后发送时间
            self.last_message_time = datetime.now()
            
            logger.info("Random message sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending random message: {e}", exc_info=True)
            
    async def run(self):
        """运行服务"""
        try:
            while True:
                if not self.is_running:
                    # 尝试重启服务
                    if await self.start():
                        logger.info("Service restarted successfully")
                    else:
                        logger.error("Failed to restart service")
                        await asyncio.sleep(60)  # 等待1分钟后重试
                        continue
                        
                # 检查是否需要发送随机消息
                now = datetime.now()
                if (not self.last_message_time or 
                    now - self.last_message_time >= timedelta(hours=3)):
                    await self.send_random_message()
                    
                await asyncio.sleep(60)  # 每分钟检查一次
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            self.is_running = False
            
def main():
    """Main entry point"""
    try:
        # 设置日志
        setup_logging()
        logger.info("Starting bot service...")
        
        # 创建主事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 创建服务实例
        service = BotService()
        
        # 启动服务
        if not loop.run_until_complete(service.start()):
            logger.error("Failed to start bot service")
            return
            
        # 确保 Telegram 服务正在运行
        if not service.telegram_core.is_running:
            logger.error("Telegram core service is not running")
            return
            
        if not service.telegram_api.is_running:
            logger.error("Telegram API service is not running")
            return
            
        # 创建启动事件
        startup_event = threading.Event()
        
        # 启动 Web 服务
        web_service = WebService(service.telegram_api, service.twitter_api)
        web_thread = threading.Thread(
            target=lambda: web_service.run(startup_event)
        )
        web_thread.daemon = True
        web_thread.start()
        
        # 等待 Web 服务启动
        if not startup_event.wait(timeout=10):
            logger.error("Web service failed to start within timeout")
            return
            
        logger.info("All services started successfully")
        
        # 运行事件循环
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping...")
        finally:
            # 停止服务
            loop.run_until_complete(service.stop())
            # 关闭事件循环
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 