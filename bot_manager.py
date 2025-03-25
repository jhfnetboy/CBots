import logging
import os
from telegram_bot import TelegramBot
from twitter_bot import TwitterBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BotManager:
    def __init__(self):
        self.telegram_bot = None
        self.twitter_bot = None
        logger.info("=== Starting Bot Manager Initialization ===")

    async def initialize(self):
        """Initialize all bots"""
        try:
            # 注册命令处理器
            logger.info("Registering command handlers...")
            from command_handlers import register_handlers
            register_handlers()
            logger.info("Command handlers registered successfully")

            # 初始化 Twitter 机器人
            logger.info("=== Starting Twitter Bot Initialization ===")
            self.twitter_bot = TwitterBot()
            await self.twitter_bot.start()
            logger.info("Twitter bot initialized successfully")
            logger.info("=== Twitter Bot Initialization Complete ===")

            # 初始化 Telegram 机器人
            logger.info("=== Starting Telegram Bot Initialization ===")
            self.telegram_bot = TelegramBot()
            await self.telegram_bot.start()
            logger.info("Telegram bot started successfully")
            logger.info("=== Telegram Bot Initialization Complete ===")
            logger.info("=== Bot Manager Initialization Complete ===")
            return True

        except Exception as e:
            logger.error(f"Error in Bot Manager initialization: {e}", exc_info=True)
            logger.error("=== Bot Manager Initialization Failed ===")
            raise

    async def run(self):
        """Run the bot main loop"""
        try:
            logger.info("Starting Telegram bot main loop...")
            if self.telegram_bot and self.telegram_bot.client:
                await self.telegram_bot.client.run_until_disconnected()
        except Exception as e:
            logger.error(f"Error in bot main loop: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop all bots"""
        try:
            if self.telegram_bot:
                await self.telegram_bot.stop()
            if self.twitter_bot:
                await self.twitter_bot.stop()
            logger.info("All bots stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bots: {e}", exc_info=True)
            raise

    def get_telegram_bot(self):
        return self.telegram_bot
    
    def get_twitter_bot(self):
        return self.twitter_bot 