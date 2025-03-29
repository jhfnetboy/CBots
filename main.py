import logging
import asyncio
import threading
from telegram_core import TelegramCore
from telegram_api import init_api, run_api
from web_service import run_web_service
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize Telegram core
        telegram_core = TelegramCore()
        await telegram_core.start()
        
        # Initialize API with Telegram core
        init_api(telegram_core)
        
        # Start API server in a separate thread
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        
        # Start web service in a separate thread
        web_thread = threading.Thread(target=run_web_service, daemon=True)
        web_thread.start()
        
        logger.info("All services started successfully")
        
        # Keep the main thread running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise
    finally:
        if telegram_core:
            await telegram_core.stop()

if __name__ == '__main__':
    asyncio.run(main()) 