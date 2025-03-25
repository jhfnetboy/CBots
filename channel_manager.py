import asyncio
import logging
from typing import List, Optional
from bot import TelegramBot

logger = logging.getLogger(__name__)

class ChannelManager:
    def __init__(self, bot: TelegramBot, max_retries: int = 3, retry_delay: int = 5):
        self.bot = bot
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.channels: List[str] = []
        self._is_initialized = False
        logger.info(f"ChannelManager initialized with max_retries={max_retries}, retry_delay={retry_delay}")

    async def initialize(self) -> bool:
        """Initialize channel list with retries"""
        logger.info("Starting channel initialization process")
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to load channels (attempt {attempt + 1}/{self.max_retries})")
                self.channels = await self.bot.get_available_channels()
                
                if not self.channels:
                    logger.warning("No channels found")
                    if attempt < self.max_retries - 1:
                        logger.info(f"Retrying in {self.retry_delay} seconds...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    logger.error("Failed to load channels after all retries")
                    return False
                
                logger.info(f"Successfully loaded {len(self.channels)} channels")
                for channel in self.channels:
                    logger.debug(f"Loaded channel: {channel}")
                self._is_initialized = True
                return True
                
            except Exception as e:
                logger.error(f"Error loading channels (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("Failed to load channels after all retries")
                    return False
        
        return False

    def get_channels(self) -> List[str]:
        """Get the current channel list"""
        if not self._is_initialized:
            logger.warning("Attempting to get channels before initialization")
        return self.channels

    @property
    def is_initialized(self) -> bool:
        """Check if channel list is initialized"""
        return self._is_initialized 