import logging
import os
from telethon import TelegramClient, events
from telethon.tl.types import Message
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv
import random
import string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramCore:
    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.target_channel = os.getenv('TELEGRAM_TARGET_CHANNEL')
        self.target_group = os.getenv('TELEGRAM_TARGET_GROUP')
        self.client = None
        self.muted_users = set()  # 记录被禁言的用户ID
        self.daily_password = self.generate_password()  # 生成每日密码
        logger.info("TelegramCore initialized")

    def generate_password(self):
        """生成随机密码"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(8))

    async def start(self):
        """Start the Telegram core service"""
        try:
            logger.info("Starting Telegram core service...")
            if not self.api_id or not self.api_hash or not self.bot_token:
                raise ValueError("Missing required environment variables")
                
            session_file = "telegram_core_session"
            self.client = TelegramClient(session_file, self.api_id, self.api_hash)
            
            await self.client.start(bot_token=self.bot_token)
            
            # 设置事件处理器
            self.setup_handlers()
            
            # 启动每日密码发送任务
            asyncio.create_task(self.start_daily_verification())
            
            # 发送上线消息
            await self.send_online_message()
            
            logger.info("Telegram core service started successfully")
        except Exception as e:
            logger.error(f"Error starting Telegram core service: {e}", exc_info=True)
            if self.client:
                await self.client.disconnect()
            raise

    async def send_online_message(self):
        """Send online message to the group"""
        try:
            if self.target_group:
                message = f"🤖 Bot is now online!\n\n今日新用户解禁密码是：{self.daily_password}"
                await self.send_message(self.target_group, message)
                logger.info("Online message sent successfully")
        except Exception as e:
            logger.error(f"Error sending online message: {str(e)}")

    def setup_handlers(self):
        """Set up event handlers"""
        try:
            # 注册新成员处理器
            @self.client.on(events.ChatAction)
            async def new_member_handler(event):
                if event.user_joined:
                    logger.info("New member handler triggered")
                    try:
                        new_member = event.user
                        if not new_member:
                            logger.warning("No new member found in event")
                            return
                        
                        chat = await event.get_chat()
                        logger.info(f"New member {new_member.first_name} (ID: {new_member.id}) joined group {chat.title}")
                        
                        # 永久禁言新成员
                        try:
                            await self.client.edit_permissions(
                                chat,
                                new_member.id,
                                until_date=None,  # 设置为 None 表示永久禁言
                                send_messages=False,
                                send_media=False,
                                send_stickers=False,
                                send_gifs=False,
                                send_games=False,
                                use_inline_bots=False
                            )
                            logger.info(f"Successfully muted new member {new_member.first_name} permanently")
                            
                            # 发送欢迎消息
                            welcome_message = (
                                f"欢迎 {new_member.first_name} 加入群组！\n"
                                "为了维护群组秩序，新成员将被禁言。\n"
                                "请私聊机器人并发送每日密码以解除禁言。"
                            )
                            await event.reply(welcome_message)
                            logger.info(f"Sent welcome message to {new_member.first_name}")
                            
                        except Exception as e:
                            logger.error(f"Error muting new member: {str(e)}")
                            
                    except Exception as e:
                        logger.error(f"Error handling new member: {str(e)}")

            # 注册私聊消息处理器
            @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
            async def private_message_handler(event):
                try:
                    user_id = event.sender_id
                    message_text = event.message.text
                    
                    # 检查是否是每日密码
                    if message_text == self.daily_password:
                        # 解除禁言
                        if self.target_group:
                            await self.client.edit_permissions(
                                self.target_group,
                                user_id,
                                until_date=None,
                                send_messages=True,
                                send_media=True,
                                send_stickers=True,
                                send_gifs=True,
                                send_games=True,
                                use_inline_bots=True
                            )
                            logger.info(f"Successfully unmuted user {user_id}")
                            await event.reply("密码正确！您的禁言已解除。")
                        else:
                            await event.reply("密码正确，但群组ID未设置，请联系管理员。")
                    else:
                        await event.reply("密码错误，请重试。")
                        
                except Exception as e:
                    logger.error(f"Error handling private message: {str(e)}")

            # 注册命令处理器
            @self.client.on(events.NewMessage(pattern='/pass'))
            async def pass_command_handler(event):
                try:
                    # 检查是否是私聊消息
                    if not event.is_private:
                        return
                    
                    # 发送每日密码
                    await event.reply(f"今日密码：{self.daily_password}")
                    logger.info(f"Sent daily password to user {event.sender_id}")
                except Exception as e:
                    logger.error(f"Error handling pass command: {str(e)}")

            # 注册所有消息处理器
            @self.client.on(events.NewMessage)
            async def message_handler(event):
                try:
                    # 获取消息信息
                    message_text = event.message.text
                    sender = await event.get_sender()
                    username = sender.username if sender else "user"
                    chat = await event.get_chat()
                    chat_title = chat.title if chat else "unknown chat"
                    
                    # 记录所有消息
                    logger.info(f"Message from {username} in {chat_title}: {message_text}")
                    
                    # 处理 @ 提及
                    if hasattr(event.message, 'mentioned') and event.message.mentioned:
                        await event.reply(f"Hi {username}, I get your message: {message_text}")
                        return
                    
                    # 处理命令
                    if message_text.startswith('/'):
                        if message_text.lower() == '/hi':
                            await event.reply("Hi, my friends，this is COS72 Bot。")
                        elif message_text.lower() == '/help':
                            help_text = (
                                "Available commands:\n"
                                "/start - Start the bot\n"
                                "/help - Show this help message\n"
                                "/hi - Say hello\n"
                                "/content - Content management\n"
                                "/price - Price information\n"
                                "/event - Event management\n"
                                "/task - Task management\n"
                                "/news - News updates\n"
                                "/PNTs - PNTs information\n"
                                "/account - Account management"
                            )
                            await event.reply(help_text)
                        elif message_text.lower() == '/pass':
                            if event.is_private:
                                await event.reply(f"今日密码：{self.daily_password}")
                            else:
                                await event.reply("请私聊机器人获取密码。")
                        else:
                            await event.reply(f"Hi {username}, you invoke function: {message_text[1:]}")
                    
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")

            logger.info("Event handlers set up successfully")
        except Exception as e:
            logger.error(f"Error setting up event handlers: {e}", exc_info=True)
            raise

    async def send_message(self, message: str, chat_id: str, reply_to: int = None):
        """Send a message to a specific chat"""
        try:
            if reply_to:
                await self.client.send_message(chat_id, message, reply_to=reply_to)
            else:
                await self.client.send_message(chat_id, message)
            logger.info(f"Message sent successfully to chat {chat_id}")
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            raise

    async def start_daily_verification(self):
        """Start the daily verification task"""
        while True:
            try:
                # 等待到下一个整点
                now = datetime.now()
                next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                await asyncio.sleep((next_hour - now).total_seconds())
                
                # 生成新的每日密码
                self.daily_password = self.generate_password()
                
                # 发送每日密码到群组
                if self.target_group:
                    await self.send_message(
                        self.target_group,
                        f"今日新用户解禁密码是：{self.daily_password}"
                    )
                
            except Exception as e:
                logger.error(f"Error in daily verification task: {e}", exc_info=True)
                await asyncio.sleep(60)  # 出错后等待1分钟再试

    async def stop(self):
        """Stop the Telegram core service"""
        try:
            if self.client:
                await self.client.disconnect()
                logger.info("Telegram core service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Telegram core service: {e}", exc_info=True)
            raise 