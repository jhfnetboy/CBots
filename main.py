import logging
import asyncio
import threading
from telegram_core import TelegramCore
from telegram_api import TelegramAPI
from twitter_core import TwitterCore
from twitter_api import TwitterAPI
from web_service import WebService
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_telegram_core():
    """运行 Telegram 核心服务"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize Telegram core
        core = TelegramCore()
        await core.start()
        
        # Initialize API with Telegram core
        telegram_api = TelegramAPI(core)  # 传入已初始化的 core
        await telegram_api.start()
        
        return telegram_api
        
    except Exception as e:
        logger.error(f"Error in Telegram core: {str(e)}")
        raise

async def run_twitter_core():
    """运行 Twitter 核心服务"""
    try:
        # Initialize Twitter core
        core = TwitterCore()
        await core.start()
        
        # Initialize API with Twitter core
        twitter_api = TwitterAPI(core)  # 传入已初始化的 core
        await twitter_api.start()
        
        return twitter_api
        
    except Exception as e:
        logger.error(f"Error in Twitter core: {str(e)}")
        raise

def run_web_service(telegram_api, twitter_api):
    """运行 Web 服务"""
    try:
        web_service = WebService(telegram_api, twitter_api)
        web_service.run_web_service()
    except Exception as e:
        logger.error(f"Error in web service: {str(e)}")
        raise

async def main():
    """主函数"""
    try:
        # 启动 Telegram 服务
        telegram_api = await run_telegram_core()
        
        # 启动 Twitter 服务
        twitter_api = await run_twitter_core()
        
        # 启动 Web 服务
        web_thread = threading.Thread(
            target=lambda: run_web_service(telegram_api, twitter_api),
            daemon=True
        )
        web_thread.start()
        
        logger.info("All services started successfully")
        
        # 保持主线程运行
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 