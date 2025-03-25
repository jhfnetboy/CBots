import logging
import asyncio
import os
from telegram_bot import TelegramBot
from twitter_bot import TwitterBot
from command_manager import command_manager, BotType

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
        self._initialized = False
        logger.info("=== Starting Bot Manager Initialization ===")

    async def initialize(self):
        """Initialize all bots"""
        try:
            # 先初始化 Twitter bot
            logger.info("Initializing Twitter bot...")
            self.twitter_bot = TwitterBot()
            await self.twitter_bot.start()
            
            # 等待一小段时间，确保 Twitter bot 完全初始化
            await asyncio.sleep(1)
            
            # 再初始化 Telegram bot
            logger.info("Initializing Telegram bot...")
            self.telegram_bot = TelegramBot()
            await self.telegram_bot.start()
            
            self._initialized = True
            logger.info("All bots initialized successfully")
            logger.info("=== Bot Manager Initialization Complete ===")
            return True

        except Exception as e:
            logger.error(f"Error initializing bots: {e}", exc_info=True)
            logger.error("=== Bot Manager Initialization Failed ===")
            # 确保在出错时清理资源
            if self.telegram_bot:
                await self.telegram_bot.stop()
            if self.twitter_bot:
                await self.twitter_bot.stop()
            raise

    async def run(self):
        """Run all bots"""
        if not self._initialized:
            await self.initialize()
            
        try:
            # 运行事件循环
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error running bots: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop all bots"""
        try:
            # 先停止 Telegram bot
            if self.telegram_bot:
                await self.telegram_bot.stop()
                
            # 等待一小段时间
            await asyncio.sleep(1)
            
            # 再停止 Twitter bot
            if self.twitter_bot:
                await self.twitter_bot.stop()
                
            logger.info("All bots stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bots: {e}", exc_info=True)
            raise

    def get_telegram_bot(self):
        """Get the Telegram bot instance"""
        return self.telegram_bot

    def get_twitter_bot(self):
        """Get the Twitter bot instance"""
        return self.twitter_bot 