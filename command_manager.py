import logging
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotType(Enum):
    TELEGRAM = "telegram"
    TWITTER = "twitter"

class CommandManager:
    def __init__(self):
        self.command_handlers = {}
        self.message_handlers = {}
        logger.info("Command Manager initialized")
    
    def register_command(self, command: str, handler, bot_type: BotType):
        """Register a command handler"""
        if bot_type not in self.command_handlers:
            self.command_handlers[bot_type] = {}
        self.command_handlers[bot_type][command] = handler
        logger.info(f"Registered command '{command}' for {bot_type.value}")
    
    def register_message_handler(self, handler, bot_type: BotType):
        """Register a message handler"""
        self.message_handlers[bot_type] = handler
        logger.info(f"Registered message handler for {bot_type.value}")
    
    async def process_command(self, command: str, event, bot):
        """Process a command"""
        try:
            bot_type = BotType.TELEGRAM if bot.__class__.__name__ == 'TelegramBot' else BotType.TWITTER
            if bot_type in self.command_handlers and command in self.command_handlers[bot_type]:
                await self.command_handlers[bot_type][command](event)
            else:
                logger.warning(f"No handler registered for command '{command}' in {bot_type.value}")
        except Exception as e:
            logger.error(f"Error processing command '{command}': {e}", exc_info=True)
    
    async def process_message(self, event, bot):
        """Process a message"""
        try:
            bot_type = BotType.TELEGRAM if bot.__class__.__name__ == 'TelegramBot' else BotType.TWITTER
            if bot_type in self.message_handlers:
                if bot_type == BotType.TELEGRAM:
                    await self.message_handlers[bot_type](event, bot)
                else:
                    await self.message_handlers[bot_type](event.message.text, event)
            else:
                logger.warning(f"No message handler registered for {bot_type.value}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

# Create a singleton instance
command_manager = CommandManager() 