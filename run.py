from app import app, bot_manager, loop, flask_thread
from bot_manager import BotManager
import logging
import asyncio
import signal
import sys
import threading
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal. Cleaning up...")
    if bot_manager and bot_manager.get_telegram_bot():
        asyncio.run_coroutine_threadsafe(bot_manager.get_telegram_bot().stop(), loop)
    if loop:
        loop.stop()
    sys.exit(0)

def run_flask():
    """Run Flask server in a separate thread"""
    port = int(os.getenv('PORT', 8872))  # 从环境变量获取端口，默认使用8872
    app.run(host='0.0.0.0', port=port, debug=False)

async def main():
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and set event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Initialize bot manager
        logger.info("=== Starting Bot Manager ===")
        bot_manager = BotManager()
        await bot_manager.initialize()
        
        # Start Flask in a separate thread
        logger.info("Starting Flask server...")
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Run the bots
        logger.info("Starting bot main loop...")
        await bot_manager.run()
        
        # Keep the main thread running
        try:
            while True:
                loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
    logger.info("Application shutdown complete") 