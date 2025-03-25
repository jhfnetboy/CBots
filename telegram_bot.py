import logging
import os
from telethon import TelegramClient, events
from telethon.tl.types import Message
from datetime import datetime, timedelta
from command_manager import command_manager, BotType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.target_channel = os.getenv('TELEGRAM_TARGET_CHANNEL')
        self.target_group = os.getenv('TELEGRAM_TARGET_GROUP')
        self.client = None
        self.verification_texts = []
        self.last_verification_time = None
        logger.info("TelegramBot initialized")

    def setup_handlers(self):
        """Set up event handlers"""
        try:
            # 注册命令处理器
            @self.client.on(events.NewMessage(pattern='/start'))
            async def start_handler(event):
                await command_manager.process_command('start', event, self)

            @self.client.on(events.NewMessage(pattern='/help'))
            async def help_handler(event):
                await command_manager.process_command('help', event, self)

            @self.client.on(events.NewMessage(pattern='/hi'))
            async def hi_handler(event):
                await command_manager.process_command('hi', event, self)

            @self.client.on(events.NewMessage(pattern='/PNTs'))
            async def pnts_handler(event):
                await command_manager.process_command('PNTs', event, self)

            # 注册消息处理器
            @self.client.on(events.NewMessage)
            async def message_handler(event):
                await command_manager.process_message(event, self)

            # 注册用户状态处理器
            @self.client.on(events.UserUpdate)
            async def user_status_handler(event):
                if event.original_update.status:
                    user = await event.get_user()
                    if user and not user.bot:
                        await event.client.send_message(
                            event.chat_id,
                            f"👋 {user.first_name} is now online!"
                        )

            logger.info("Telegram bot event handlers set up successfully")
        except Exception as e:
            logger.error(f"Error setting up event handlers: {e}", exc_info=True)
            raise

    async def start(self):
        """Start the Telegram bot"""
        try:
            logger.info("Starting Telegram bot...")
            self.client = TelegramClient('bot_session', self.api_id, self.api_hash)
            await self.client.start(bot_token=self.bot_token)
            
            # 设置事件处理器
            self.setup_handlers()
            
            logger.info("Telegram bot started successfully")
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop the Telegram bot"""
        try:
            if self.client:
                await self.client.disconnect()
                logger.info("Telegram bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}", exc_info=True)
            raise

    async def send_message(self, chat_id: str, message: str):
        """Send a message to a specific chat"""
        try:
            await self.client.send_message(chat_id, message)
            logger.info(f"Message sent successfully to chat {chat_id}")
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            raise

    async def generate_verification_text(self):
        """Generate a verification text"""
        try:
            current_time = datetime.now()
            if not self.last_verification_time or (current_time - self.last_verification_time).days >= 1:
                self.verification_texts = []
                self.last_verification_time = current_time
            
            if not self.verification_texts:
                # 生成新的验证文本
                verification_text = f"Verification text for {current_time.strftime('%Y-%m-%d')}"
                self.verification_texts.append(verification_text)
            
            return self.verification_texts[0]
        except Exception as e:
            logger.error(f"Error generating verification text: {e}", exc_info=True)
            return None

    async def send_daily_verification(self):
        """Send daily verification text"""
        try:
            verification_text = await self.generate_verification_text()
            if verification_text and self.target_group:
                await self.send_message(self.target_group, verification_text)
                logger.info("Daily verification text sent successfully")
        except Exception as e:
            logger.error(f"Error sending daily verification: {e}", exc_info=True)
            raise

    async def handle_new_user(self, user_id: int, username: str):
        """Handle new user verification"""
        try:
            verification_text = await self.generate_verification_text()
            if verification_text:
                await self.client.send_message(
                    user_id,
                    f"Welcome {username}! Please verify yourself by sending this text: {verification_text}"
                )
                logger.info(f"Verification message sent to new user {username}")
        except Exception as e:
            logger.error(f"Error handling new user: {e}", exc_info=True)
            raise