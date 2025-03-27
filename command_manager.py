import logging
from enum import Enum
from typing import Dict, Callable, Any, Set

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
        self.processed_messages: Set[str] = set()  # 用于跟踪已处理的消息
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

    def _get_message_id(self, event: Any) -> str:
        """获取消息的唯一标识符"""
        if hasattr(event, 'message') and hasattr(event.message, 'id'):
            return f"{event.message.chat_id}_{event.message.id}"
        return None

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
                
            # 检查消息是否已处理
            message_id = self._get_message_id(event)
            if message_id and message_id in self.processed_messages:
                logger.info(f"Message {message_id} already processed, skipping")
                return
                
            handler = self.command_handlers[bot_type][command]
            await handler(event)
            
            # 标记消息为已处理
            if message_id:
                self.processed_messages.add(message_id)
                
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
                
            # 检查消息是否已处理
            message_id = self._get_message_id(event)
            if message_id and message_id in self.processed_messages:
                logger.info(f"Message {message_id} already processed, skipping")
                return
                
            handler = self.message_handlers[bot_type]
            await handler(event)
            
            # 标记消息为已处理
            if message_id:
                self.processed_messages.add(message_id)
                
            logger.info("Message processed successfully")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

# Create a global instance
command_manager = CommandManager() 