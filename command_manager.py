import logging
from enum import Enum
from typing import Dict, Callable, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotType(Enum):
    TELEGRAM = 'telegram'
    TWITTER = 'twitter'

class CommandManager:
    def __init__(self):
        self.command_handlers: Dict[BotType, Dict[str, Callable]] = {
            BotType.TELEGRAM: {},
            BotType.TWITTER: {}
        }
        self.message_handlers: Dict[BotType, Callable] = {}
        logger.info("Command Manager initialized")

    def register_command(self, command: str, handler: Callable, bot_type: BotType):
        """Register a command handler"""
        if bot_type not in self.command_handlers:
            self.command_handlers[bot_type] = {}
        self.command_handlers[bot_type][command] = handler
        logger.info(f"Registered command '{command}' for {bot_type.value}")

    def register_message_handler(self, handler: Callable, bot_type: BotType):
        """Register a message handler"""
        self.message_handlers[bot_type] = handler
        logger.info(f"Registered message handler for {bot_type.value}")

    async def process_command(self, command: str, event: Any, bot: Any):
        """Process a command"""
        try:
            bot_type = BotType.TELEGRAM if hasattr(bot, 'client') else BotType.TWITTER
            
            if bot_type not in self.command_handlers:
                logger.error(f"No command handlers registered for {bot_type.value}")
                return
                
            if command not in self.command_handlers[bot_type]:
                logger.error(f"Command '{command}' not found for {bot_type.value}")
                return
                
            handler = self.command_handlers[bot_type][command]
            await handler(event)
            logger.info(f"Command '{command}' processed successfully")
        except Exception as e:
            logger.error(f"Error processing command '{command}': {bot_type}", exc_info=True)

    async def process_message(self, event: Any, bot: Any):
        """Process a message"""
        try:
            bot_type = BotType.TELEGRAM if hasattr(bot, 'client') else BotType.TWITTER
            
            if bot_type not in self.message_handlers:
                logger.warning(f"No message handler registered for {bot_type.value}")
                return
                
            handler = self.message_handlers[bot_type]
            await handler(event)
            logger.info("Message processed successfully")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

# Create a global instance
command_manager = CommandManager() 