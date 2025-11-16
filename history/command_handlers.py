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
/content - Show content list
/hi - Say hello and onboarding page
/price - Query price of top 10 in CoinMarketCap
/event - Query community events info
/task - Query community task info
/news - Query news information
/PNTs - Query PNTs balance and more info
/account - Initiate a new AirAccount or get your AirAccount public info (private msg)
/help - Show this help message
        """
        await event.reply(help_text)
        logger.info(f"Help command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing help command: {e}", exc_info=True)

async def telegram_hi(event, bot: TelegramBot):
    """Handle /hi command for Telegram"""
    try:
        # 获取发送者信息
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "User"
        await event.reply(f"Welcome {sender_name}! 👋")
        logger.info(f"Hi command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing hi command: {e}", exc_info=True)

async def telegram_pnts(event, bot: TelegramBot):
    """Handle /PNTs command for Telegram"""
    try:
        # 获取发送者信息
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "User"
        await event.reply(f"Hi {sender_name}, I got your function call: PNTs")
        logger.info(f"PNTs command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing PNTs command: {e}", exc_info=True)

async def telegram_content(event, bot: TelegramBot):
    """Handle /content command for Telegram"""
    try:
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "User"
        await event.reply(f"Hi {sender_name}, I got your function call: content")
        logger.info(f"Content command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing content command: {e}", exc_info=True)

async def telegram_price(event, bot: TelegramBot):
    """Handle /price command for Telegram"""
    try:
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "User"
        await event.reply(f"Hi {sender_name}, I got your function call: price")
        logger.info(f"Price command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing price command: {e}", exc_info=True)

async def telegram_event(event, bot: TelegramBot):
    """Handle /event command for Telegram"""
    try:
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "User"
        await event.reply(f"Hi {sender_name}, I got your function call: event")
        logger.info(f"Event command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing event command: {e}", exc_info=True)

async def telegram_task(event, bot: TelegramBot):
    """Handle /task command for Telegram"""
    try:
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "User"
        await event.reply(f"Hi {sender_name}, I got your function call: task")
        logger.info(f"Task command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing task command: {e}", exc_info=True)

async def telegram_news(event, bot: TelegramBot):
    """Handle /news command for Telegram"""
    try:
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "User"
        await event.reply(f"Hi {sender_name}, I got your function call: news")
        logger.info(f"News command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing news command: {e}", exc_info=True)

async def telegram_account(event, bot: TelegramBot):
    """Handle /account command for Telegram"""
    try:
        sender = await event.get_sender()
        sender_name = sender.first_name if sender else "User"
        await event.reply(f"Hi {sender_name}, I got your function call: account")
        logger.info(f"Account command processed for user {event.sender_id}")
    except Exception as e:
        logger.error(f"Error processing account command: {e}", exc_info=True)

async def telegram_message(event, bot: TelegramBot):
    """Handle regular messages for Telegram"""
    try:
        # 检查是否是@机器人的消息
        if event.mentioned:
            # 获取发送者信息
            sender = await event.get_sender()
            sender_name = sender.first_name if sender else "User"
            
            # 如果是@机器人的消息，回复用户
            await event.reply(f"Hi {sender_name}, I got your message: {event.text}")
        # 其他消息只记录，不回复
        logger.info(f"Message received from user {event.sender_id}: {event.text}")
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
        command_manager.register_command('content', telegram_content, BotType.TELEGRAM)
        command_manager.register_command('price', telegram_price, BotType.TELEGRAM)
        command_manager.register_command('event', telegram_event, BotType.TELEGRAM)
        command_manager.register_command('task', telegram_task, BotType.TELEGRAM)
        command_manager.register_command('news', telegram_news, BotType.TELEGRAM)
        command_manager.register_command('account', telegram_account, BotType.TELEGRAM)
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