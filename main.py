import logging
import asyncio
import threading
from telegram_core import TelegramCore
from telegram_api import TelegramAPI
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
        telegram_api = TelegramAPI()
        
        # Start web service in a separate thread
        web_thread = threading.Thread(
            target=lambda: run_web_service(telegram_api),
            daemon=True
        )
        web_thread.start()
        
        logger.info("Telegram core and web service started successfully")
        
        # Keep the main thread running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in Telegram core: {str(e)}")
        raise

def run_web_service(telegram_api):
    """运行 Web 服务"""
    try:
        web_service = WebService(telegram_api)
        web_service.run_web_service()
    except Exception as e:
        logger.error(f"Error in web service: {str(e)}")
        raise

def main():
    """主函数"""
    try:
        # 创建并启动 Telegram 核心服务线程
        telegram_thread = threading.Thread(
            target=lambda: asyncio.run(run_telegram_core()),
            daemon=True
        )
        telegram_thread.start()
        
        # 等待线程结束
        telegram_thread.join()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 