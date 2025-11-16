import tweepy_patch  # 添加补丁导入
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
from flask import Flask
from flask_cors import CORS

# 加载环境变量
load_dotenv()

# 从web_routes导入VERSION
try:
    from web_routes import VERSION
except ImportError:
    VERSION = "unknown"

# 全局变量
telegram_client = None

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
        """启动服务"""
        try:
            # 启动 Telegram 服务
            logger.info("Starting Telegram core service...")
            if not await self.telegram_core.start():
                logger.error("Failed to start Telegram service")
                return False
            logger.info(f"Telegram core service status - is_running: {self.telegram_core.is_running}")
                
            # 启动 Twitter 服务
            try:
                if not await self.twitter_core.start():
                    logger.warning("Failed to start Twitter service, continuing without Twitter functionality")
            except Exception as e:
                logger.warning(f"Twitter service failed to start: {e}, continuing without Twitter functionality")
            
            # 启动 Telegram API 服务
            logger.info("Starting Telegram API service...")
            if not await self.telegram_api.start():
                logger.error("Failed to start Telegram API service")
                return False
            logger.info(f"Telegram API service status - is_running: {self.telegram_api.is_running}")
            
            # 暂时注释掉上线消息
            # await self.message_handlers.send_online_message()
            
            self.is_running = True
            logger.info("Bot service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting bot service: {e}", exc_info=True)
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
            
async def start_web_service():
    """Start the web service"""
    try:
        # 获取环境变量
        mode = os.environ.get('MODE', 'dev')
        if mode == 'prd':
            port = int(os.environ.get('PRD_PORT', 8872))
        else:
            # 尝试使用一个不太可能被占用的端口
            port = int(os.environ.get('DEV_PORT', 9873))
        
        logger.info(f"Starting web service in {mode} mode on port {port}")
        
        # Create the Flask app
        app = Flask(__name__, 
                   template_folder='templates',
                   static_folder='static',
                   static_url_path='')
        
        # Set CORS policy
        CORS(app)
        
        # Init web routes
        from web_routes import init_web_routes, set_main_loop
        set_main_loop(asyncio.get_event_loop())
        init_web_routes(app, telegram_client)
        
        # Run the app
        web_thread = threading.Thread(target=app.run, kwargs={
            'host': '0.0.0.0',
            'port': port,
            'debug': False,
            'use_reloader': False
        })
        web_thread.daemon = True
        web_thread.start()
        
        logger.info(f"Web service started on port {port}")
        return True
    except Exception as e:
        logger.error(f"Error starting web service: {e}")
        return False

def main():
    """Main entry point"""
    try:
        # 设置日志
        setup_logging()
        logger.info("Starting bot service...")
        logger.info(f"Bot version: {VERSION}")
        
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
            
        # 确保 Twitter 服务正在运行
        logger.info(f"Twitter core service status - is_running: {service.twitter_core.is_running}")
        logger.info(f"Twitter API service status - is_running: {service.twitter_api.is_running}")
            
        # 设置全局变量让其他模块可以访问
        global telegram_client
        telegram_client = service.telegram_core.client
            
        # 启动 Web 服务
        if not loop.run_until_complete(start_web_service()):
            logger.error("Web service failed to start")
            return
            
        logger.info("All services started successfully")
        logger.info(f"Bot version: {VERSION}")
        
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