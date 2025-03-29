import asyncio
import logging
from telegram_core import TelegramCore
from twitter_core import TwitterCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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