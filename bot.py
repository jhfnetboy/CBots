from telethon import TelegramClient, events
from config import API_ID, API_HASH, HELP_MESSAGE, TARGET_CHANNEL, TARGET_GROUP, BOT_TOKEN, COMMANDS, NEW_USER_VERIFICATION
import asyncio
import aiohttp
import os
from pathlib import Path
import logging
import random
import string
from datetime import datetime, timedelta
import tempfile

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        logger.info(f"Initializing bot with API_ID: {API_ID}")
        # Use memory session instead of file session
        self.client = TelegramClient(
            'bot_session',
            API_ID,
            API_HASH,
            device_model="Bot",
            system_version="1.0",
            app_version="1.0",
            lang_code="en"
        )
        self.TARGET_CHANNEL = TARGET_CHANNEL
        self.TARGET_GROUP = TARGET_GROUP
        self.daily_verification_text = None
        self.verification_date = None
        self.setup_handlers()

    def generate_verification_text(self):
        """生成每日验证文本"""
        length = random.randint(
            NEW_USER_VERIFICATION['message_length']['min'],
            NEW_USER_VERIFICATION['message_length']['max']
        )
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for _ in range(length))

    async def send_daily_verification(self):
        """Send daily verification text"""
        try:
            today = datetime.now().date()
            if self.verification_date != today:
                self.daily_verification_text = self.generate_verification_text()
                self.verification_date = today
                message = f"🔐 Daily Verification Text:\n\n{self.daily_verification_text}\n\nPlease send this text in private chat to unmute."
                await self.send_message(message, self.TARGET_GROUP)
                logger.info(f"Sent daily verification text: {self.daily_verification_text}")
        except Exception as e:
            logger.error(f"Error sending daily verification: {e}")

    def setup_handlers(self):
        """设置事件处理器"""
        # 处理新消息
        @self.client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            try:
                logger.info("=== New Message Received ===")
                logger.info(f"Message text: {event.text}")
                logger.info(f"From user: {event.sender_id}")
                logger.info(f"Chat: {event.chat_id}")
                logger.info(f"Bot mentioned: {event.message.mentioned}")
                logger.info("==========================")
                
                # 检查是否是@bot的消息
                if event.message.mentioned or event.text.startswith('/'):
                    logger.info("Processing command or mentioned message")
                    await self.process_command(event)
            except Exception as e:
                logger.error(f"Error handling new message: {e}")

        # 处理新成员加入
        @self.client.on(events.ChatAction)
        async def handle_new_member(event):
            try:
                if event.user_joined and NEW_USER_VERIFICATION['enabled']:
                    user = await event.get_user()
                    chat = await event.get_chat()
                    
                    logger.info(f"New user joined: {user.id} in chat {chat.id}")
                    
                    # Mute new user
                    try:
                        await self.client.edit_permissions(
                            chat,
                            user,
                            until_date=datetime.now() + timedelta(seconds=NEW_USER_VERIFICATION['mute_duration']),
                            send_messages=False
                        )
                        logger.info(f"Muted user {user.id} for {NEW_USER_VERIFICATION['mute_duration']} seconds")
                        
                        # Send welcome message
                        welcome_message = (
                            f"👋 Welcome {user.first_name} to the group!\n\n"
                            f"🔒 You have been temporarily muted for {NEW_USER_VERIFICATION['mute_duration']//3600} hours.\n"
                            f"💬 Please send today's verification text in private chat to @{self.client.me.username} to unmute."
                        )
                        await self.send_message(welcome_message, chat.id)
                    except Exception as e:
                        logger.error(f"Error muting new user: {e}")
            except Exception as e:
                logger.error(f"Error handling new member: {e}")

        # 处理私聊消息
        @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def handle_private_message(event):
            try:
                if NEW_USER_VERIFICATION['enabled'] and self.daily_verification_text:
                    user = await event.get_user()
                    message = event.text.strip()
                    
                    logger.info(f"Received private message from {user.id}: {message}")
                    
                    if message == self.daily_verification_text:
                        # Verification successful, unmute user
                        try:
                            await self.client.edit_permissions(
                                self.TARGET_GROUP,
                                user,
                                until_date=None,
                                send_messages=True
                            )
                            await event.reply("✅ Verification successful! You have been unmuted.")
                            logger.info(f"Unmuted user {user.id} after verification")
                        except Exception as e:
                            logger.error(f"Error unmuting user: {e}")
                            await event.reply("❌ Failed to unmute. Please contact administrator.")
                    else:
                        await event.reply("❌ Incorrect verification text. Please try again.")
            except Exception as e:
                logger.error(f"Error handling private message: {e}")

    async def process_command(self, event):
        """处理命令和@消息"""
        try:
            message = event.message.text.lower()
            sender = await event.get_sender()
            chat = await event.get_chat()
            
            logger.info(f"Processing command: {message}")
            logger.info(f"From sender: {sender}")
            logger.info(f"In chat: {chat}")
            
            # 如果是@消息，移除@部分
            if event.message.mentioned:
                message = message.split('@')[0].strip()
            
            # 处理命令
            if message.startswith('/'):
                command = message.split()[0]
                if command in COMMANDS:
                    response = await self.handle_command(command, event)
                    await event.reply(response)
                else:
                    await event.reply(HELP_MESSAGE)
            else:
                # 处理普通@消息
                await event.reply(HELP_MESSAGE)
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            await event.reply("Sorry, I encountered an error processing your message.")

    async def handle_command(self, command, event):
        """Handle specific commands"""
        try:
            logger.info(f"Handling command: {command}")
            if command == '/help':
                return HELP_MESSAGE
            elif command == '/content':
                return "Content list will be available soon!"
            elif command == '/PNTs':
                return "You called the PNTs function"
            elif command == '/hi':
                return "Hello! How can I help you today?"
            elif command == '/queryPrice':
                return "You called the Price function"
            elif command == '/queryVolume':
                return "You called the Volume function"
            elif command == '/queryMarket':
                return "You called the Market function"
            elif command == '/queryNews':
                return "You called the News function"
            elif command == '/queryStats':
                return "You called the Stats function"
            else:
                return HELP_MESSAGE
        except Exception as e:
            logger.error(f"Error in handle_command: {e}")
            return "Sorry, I encountered an error processing your command."

    async def start(self):
        """Start bot"""
        try:
            # Start the client
            await self.client.start(bot_token=BOT_TOKEN)
            logger.info("Bot started successfully")
            
            # Get bot info
            me = await self.client.get_me()
            logger.info(f"Bot is running as: {me}")
            logger.info(f"Bot username: {me.username}")
            logger.info(f"Bot ID: {me.id}")
            logger.info("Bot is ready to receive messages!")
            
            # Send daily verification text
            await self.send_daily_verification()
            
            # Schedule daily verification
            asyncio.create_task(self.schedule_daily_verification())
            
            # Keep the bot running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            if "ImportBotAuthorizationRequest" in str(e):
                logger.warning("Rate limit hit, waiting before retrying...")
                # Wait for 30 minutes before retrying
                await asyncio.sleep(1800)
                # Retry starting the bot
                await self.start()
            else:
                logger.error(f"Error starting bot: {e}")
                raise

    async def schedule_daily_verification(self):
        """设置每日发送验证文本的定时任务"""
        while True:
            try:
                # 等待到第二天凌晨
                now = datetime.now()
                tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                await asyncio.sleep((tomorrow - now).total_seconds())
                
                # 发送新的验证文本
                await self.send_daily_verification()
            except Exception as e:
                logger.error(f"Error in daily verification schedule: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试

    async def stop(self):
        """停止bot"""
        try:
            await self.client.disconnect()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            raise

    async def send_message(self, message, target, reply_to=None):
        """Send message to a specific chat"""
        try:
            # Get the chat entity
            chat = await self.client.get_entity(target)
            
            # Send message with optional reply_to parameter
            await self.client.send_message(
                chat,
                message,
                reply_to=reply_to
            )
            
            logger.info(f"Message sent successfully to {target}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            raise

    async def get_available_channels(self):
        """Get list of available channels and groups"""
        channels = []
        try:
            logger.info("Starting to get available channels...")
            
            # Get bot's group
            if self.TARGET_GROUP:
                try:
                    logger.info(f"Attempting to get group info for {self.TARGET_GROUP}")
                    group = await self.client.get_entity(self.TARGET_GROUP)
                    channel_info = {
                        'id': str(group.id),
                        'title': group.title,
                        'username': group.username,
                        'type': 'group'
                    }
                    channels.append(channel_info)
                    logger.info(f"Successfully added group: {group.title} (ID: {group.id})")
                except Exception as e:
                    logger.error(f"Error getting group info for {self.TARGET_GROUP}: {str(e)}")

            # Get bot's channel
            if self.TARGET_CHANNEL:
                try:
                    logger.info(f"Attempting to get channel info for {self.TARGET_CHANNEL}")
                    channel = await self.client.get_entity(self.TARGET_CHANNEL)
                    channel_info = {
                        'id': str(channel.id),
                        'title': channel.title,
                        'username': channel.username,
                        'type': 'channel'
                    }
                    channels.append(channel_info)
                    logger.info(f"Successfully added channel: {channel.title} (ID: {channel.id})")
                except Exception as e:
                    logger.error(f"Error getting channel info for {self.TARGET_CHANNEL}: {str(e)}")

            # Get bot's dialogs
            logger.info("Starting to get bot's dialogs...")
            dialog_count = 0
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    try:
                        channel_info = {
                            'id': str(dialog.id),
                            'title': dialog.name,
                            'username': dialog.entity.username,
                            'type': 'channel' if dialog.is_channel else 'group'
                        }
                        channels.append(channel_info)
                        dialog_count += 1
                        logger.debug(f"Added dialog: {dialog.name} (ID: {dialog.id})")
                    except Exception as e:
                        logger.error(f"Error adding dialog {dialog.name}: {str(e)}")
                        continue

            logger.info(f"Channel loading completed. Total channels: {len(channels)}")
            logger.info(f"Target group: {self.TARGET_GROUP}")
            logger.info(f"Target channel: {self.TARGET_CHANNEL}")
            logger.info(f"Additional dialogs found: {dialog_count}")
            
            if not channels:
                logger.warning("No channels were loaded!")
            
            return channels

        except Exception as e:
            logger.error(f"Critical error in get_available_channels: {str(e)}")
            return channels