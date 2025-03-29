import asyncio
import logging
import threading
from telegram_core import TelegramCore
from twitter_core import TwitterCore
from api import BotAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_api(telegram_core, twitter_core):
    """在单独的线程中运行API服务"""
    api = BotAPI(telegram_core, twitter_core)
    api.run()

async def main():
    """启动所有机器人服务"""
    try:
        # 初始化服务
        telegram_core = TelegramCore()
        twitter_core = TwitterCore()
        
        # 启动服务
        telegram_started = await telegram_core.start()
        twitter_started = await twitter_core.start()
        
        if not telegram_started or not twitter_started:
            logger.error("Failed to start services")
            return
            
        logger.info("All services started successfully")
        
        # 在单独的线程中启动API服务
        api_thread = threading.Thread(
            target=run_api,
            args=(telegram_core, twitter_core)
        )
        api_thread.daemon = True
        api_thread.start()
        
        # 设置事件处理器
        telegram_core.client.add_event_handler(
            telegram_core.message_handlers.handle_new_member,
            telegram_core.events.ChatAction
        )
        
        # 注册命令处理器
        @telegram_core.client.on(telegram_core.events.NewMessage(pattern='/hi'))
        async def hi_handler(event):
            await telegram_core.message_handlers.handle_hi_command(event)
            
        @telegram_core.client.on(telegram_core.events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await telegram_core.message_handlers.handle_start_command(event)
            
        @telegram_core.client.on(telegram_core.events.NewMessage(pattern='/help'))
        async def help_handler(event):
            await telegram_core.message_handlers.handle_help_command(event)
            
        # 处理 @bot 消息
        @telegram_core.client.on(telegram_core.events.NewMessage(func=lambda e: e.mentioned))
        async def mention_handler(event):
            await telegram_core.message_handlers.handle_mention(event)
            
        # 处理私聊消息
        @telegram_core.client.on(telegram_core.events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def private_message_handler(event):
            await telegram_core.message_handlers.handle_private_message(event)
            
        # 发送上线消息
        await telegram_core.message_handlers.send_online_message()
        
        # 保持服务运行
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        # 停止服务
        await telegram_core.stop()
        await twitter_core.stop()

if __name__ == "__main__":
    asyncio.run(main()) 