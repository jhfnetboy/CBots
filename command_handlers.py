import logging
from command_manager import command_manager, BotType
from telegram_bot import TelegramBot
from twitter_bot import TwitterBot
from telethon.tl.types import Message
from telethon import events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram command handlers
async def telegram_start(event, bot: TelegramBot):
    """Handle /start command for Telegram"""
    try:
        await event.reply("Hello! I'm your Telegram bot. How can I help you?")
        logger.info(f"Start command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing start command: {e}", exc_info=True)

async def telegram_help(event, bot: TelegramBot):
    """Handle /help command for Telegram"""
    try:
        help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/hi - Say hello
/PNTs - Call the PNTs function
        """
        await event.reply(help_text)
        logger.info(f"Help command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing help command: {e}", exc_info=True)

async def telegram_hi(event, bot: TelegramBot):
    """Handle /hi command for Telegram"""
    try:
        await event.reply(f"Hi {event.sender.first_name}!")
        logger.info(f"Hi command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing hi command: {e}", exc_info=True)

async def telegram_pnts(event, bot: TelegramBot):
    """Handle /PNTs command for Telegram"""
    try:
        await event.reply(f"Hi {event.sender.first_name}! You called the PNTs function.")
        logger.info(f"PNTs command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing PNTs command: {e}", exc_info=True)

async def telegram_message(event, bot: TelegramBot):
    """Handle regular messages for Telegram"""
    try:
        # 检查是否是回复消息
        if event.reply_to:
            # 获取被回复的消息
            replied_msg = await event.get_reply_message()
            if replied_msg and replied_msg.sender_id == (await bot.client.get_me()).id:
                # 如果是回复机器人的消息
                await event.reply(f"I received your message: {event.text} from {event.sender.first_name}")
            else:
                await event.reply("I received your message!")
        else:
            await event.reply("I received your message!")
        logger.info(f"Message processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)

async def telegram_user_online(event, bot: TelegramBot):
    """Handle user online status"""
    try:
        user = await event.get_user()
        if user and not user.bot:
            await event.client.send_message(
                event.chat_id,
                f"👋 {user.first_name} is now online!"
            )
    except Exception as e:
        logger.error(f"Error handling user online status: {e}", exc_info=True)

# Twitter command handlers
async def twitter_start(event, bot: TwitterBot):
    """Handle /start command for Twitter"""
    try:
        await event.reply("Hello! I'm your Twitter bot. How can I help you?")
        logger.info(f"Start command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing start command: {e}", exc_info=True)

async def twitter_help(event, bot: TwitterBot):
    """Handle /help command for Twitter"""
    try:
        help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/hi - Say hello
        """
        await event.reply(help_text)
        logger.info(f"Help command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing help command: {e}", exc_info=True)

async def twitter_hi(event, bot: TwitterBot):
    """Handle /hi command for Twitter"""
    try:
        await event.reply(f"Hi {event.sender.screen_name}!")
        logger.info(f"Hi command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing hi command: {e}", exc_info=True)

async def twitter_message(event, bot: TwitterBot):
    """Handle regular messages for Twitter"""
    try:
        await event.reply("I received your message!")
        logger.info(f"Message processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)

def register_handlers():
    """Register all command handlers"""
    try:
        # 注册 Telegram 命令处理器
        command_manager.register_command('start', telegram_start, BotType.TELEGRAM)
        command_manager.register_command('help', telegram_help, BotType.TELEGRAM)
        command_manager.register_command('hi', telegram_hi, BotType.TELEGRAM)
        command_manager.register_command('PNTs', telegram_pnts, BotType.TELEGRAM)
        command_manager.register_message_handler(telegram_message, BotType.TELEGRAM)
        
        # 注册 Twitter 命令处理器
        command_manager.register_command('start', twitter_start, BotType.TWITTER)
        command_manager.register_command('help', twitter_help, BotType.TWITTER)
        command_manager.register_command('hi', twitter_hi, BotType.TWITTER)
        command_manager.register_message_handler(twitter_message, BotType.TWITTER)
        
        logger.info("All command handlers registered successfully")
    except Exception as e:
        logger.error(f"Error registering command handlers: {e}", exc_info=True)
        raise 