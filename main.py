#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MuteBot 主程序入口
- 本地运行时，启动 BotAPICore 的 polling 模式进行测试。
- 在 PythonAnywhere 等 WSGI 环境部署时，此文件不直接运行，由 web_service.py 处理 webhook。
"""

import logging
import os
import sys
from dotenv import load_dotenv
import signal

# Load environment variables first
load_dotenv()

# --- Logging Setup ---
def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'), # Log to file
            logging.StreamHandler(sys.stdout) # Also log to console
        ]
    )
setup_logging()
logger = logging.getLogger(__name__)
# --------------------

# Import BotAPICore after logging is set up
try:
    from bot_api_core import BotAPICore
except ImportError as e:
    logger.error(f"Failed to import BotAPICore. Make sure dependencies are installed: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error during BotAPICore import: {e}")
    sys.exit(1)

# --- Global Variables & Signal Handling ---
running = True
bot_instance = None

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info("Shutdown signal received. Stopping bot...")
    running = False
    if bot_instance and hasattr(bot_instance, 'updater'):
        try:
            bot_instance.updater.stop() # Stop polling gracefully
            logger.info("Bot polling stopped.")
        except Exception as e:
            logger.error(f"Error stopping bot updater: {e}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler) # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # Handle kill command
# -----------------------------------------

# --- Main Execution Logic ---
def main():
    """Main function to start the bot in polling mode if run locally"""
    global bot_instance
    
    # Check if we should run in local polling mode
    # We assume we are NOT on PythonAnywhere if 'PYTHONANYWHERE_DOMAIN' is not set.
    # Alternatively, use a specific flag like RUN_MODE=local.
    run_local = os.getenv('PYTHONANYWHERE_DOMAIN') is None
    # run_local = os.getenv('RUN_MODE', 'webhook').lower() == 'local' # Alternative check

    if run_local:
        logger.info("Running in LOCAL POLLING mode.")
        try:
            bot_instance = BotAPICore()
            logger.info(f"Starting polling for Bot version {bot_instance.version}...")
            bot_instance.updater.start_polling()
            logger.info("Bot is now polling for updates.")
            bot_instance.updater.idle() # Keep the script running until interrupted
        except ValueError as e:
             logger.error(f"Configuration error: {e}")
        except Exception as e:
            logger.error(f"Error starting bot in polling mode: {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        logger.info("Running in PRODUCTION (Webhook) mode. This script will exit.")
        logger.info("The bot should be run via the WSGI server configured in web_service.py.")
        # Do nothing here, web_service.py + WSGI server handles it.

if __name__ == '__main__':
    main()
# -------------------------- 