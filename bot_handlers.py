import os
import logging
import random
import string
from datetime import datetime, timedelta
from telethon.tl.types import ChatBannedRights

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self):
        self.muted_users = set()  # 改为集合，只记录被禁言的用户ID
        self.default_group_id = os.getenv('TELEGRAM_DEFAULT_GROUP')  # 使用环境变量中的群组ID
        self.daily_password = self.generate_password()  # 生成每日密码

    def generate_password(self):
        """生成随机密码"""
        # 生成8位随机字符串，包含大小写字母和数字
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(8))

    async def send_online_message(self, client):
        """Send online message to the group"""
        try:
            # Get group ID from environment variable
            group_id = os.getenv('TELEGRAM_GROUP')
            if not group_id:
                logger.error("TELEGRAM_GROUP not found in environment variables")
                return
                
            # Send online message with daily password
            message = f"🤖 Bot is now online!\n\n今日新用户解禁密码是：{self.daily_password}"
            await client.send_message(group_id, message)
            logger.info("Online message sent successfully")
        except Exception as e:
            logger.error(f"Error sending online message: {str(e)}")

    async def send_daily_password(self, client):
        """Send daily password to default group"""
        try:
            if not self.default_group_id:
                logger.error("TELEGRAM_DEFAULT_GROUP not set in environment variables")
                return
                
            # 生成新的每日密码
            self.daily_password = self.generate_password()
            await client.send_message(self.default_group_id, f"今日密码：{self.daily_password}")
            logger.info(f"Sent daily password to group {self.default_group_id}")
        except Exception as e:
            logger.error(f"Error sending daily password: {str(e)}")

    async def handle_message(self, event, command_manager):
        """Handle new messages"""
        try:
            message_text = event.message.text
            user_id = event.sender_id
            
            # Get username safely
            try:
                username = event.sender.username or "user"
            except:
                username = "user"
            
            # Check if user is muted
            if user_id in self.muted_users:
                await event.reply("您当前处于禁言状态，请私聊机器人发送每日密码以解除禁言。")
                return
            
            # Handle commands
            if message_text.startswith('/'):
                if message_text.lower() == '/pass':
                    await event.reply(f"今日密码：{self.daily_password}")
                    return
                response = await command_manager.handle_command(message_text)
                if response:
                    await event.reply(response)
                return
            
            # Handle mentions
            if hasattr(event.message, 'mentioned') and event.message.mentioned:
                await event.reply(f"Hi {username}, I get your message: {message_text}")
                return
            
            # For other messages, just log them
            logger.info(f"Received message from {username}: {message_text}")
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def handle_new_member(self, event, client):
        """Handle new member joined event"""
        try:
            # Get the new member
            new_member = event.new_participant
            if not new_member:
                return
            
            # Get chat information
            chat = await event.get_chat()
            chat_id = event.chat_id
            
            # Get bot information
            bot = await client.get_me()
            bot_id = bot.id
            
            # Check if the new member is not a bot
            if not new_member.bot:
                # Restrict the new member for 4 hours
                until_date = datetime.now() + timedelta(hours=4)
                await client.edit_permissions(
                    chat_id,
                    new_member.id,
                    until_date=until_date,
                    send_messages=False,
                    send_media=False,
                    send_stickers=False,
                    send_gifs=False,
                    send_games=False,
                    use_inline_bots=False
                )
                
                # Send welcome message with instructions
                welcome_message = (
                    f"Welcome {new_member.first_name}! 👋\n\n"
                    f"You are currently muted for 4 hours.\n"
                    f"To unmute yourself, please:\n"
                    f"1. Send a private message to @{bot.username}\n"
                    f"2. Use the /password command\n"
                    f"3. Enter today's password\n\n"
                    f"Today's password: {self.daily_password}"
                )
                
                await event.reply(welcome_message)
                logger.info(f"Restricted new member {new_member.id} in chat {chat_id}")
                
        except Exception as e:
            logger.error(f"Error handling new member: {str(e)}")

    async def handle_private_message(self, event, client):
        """Handle private messages"""
        try:
            user_id = event.sender_id
            message_text = event.message.text
            
            # Check if user is muted
            if user_id in self.muted_users:
                # Check if message is the daily password
                if message_text == self.daily_password:
                    # Unmute user in default group
                    await client.edit_permissions(self.default_group_id, user_id, send_messages=True)
                    logger.info(f"Unmuted user {user_id} in group {self.default_group_id}")
                    
                    # Remove user from muted users set
                    self.muted_users.remove(user_id)
                    
                    await event.reply("密码正确！您的禁言已解除。")
                else:
                    await event.reply("密码错误，请重试。")
        except Exception as e:
            logger.error(f"Error handling private message: {str(e)}")

    async def check_unmute_users(self, client):
        """Check and unmute users whose time has expired"""
        for user_id, unmute_time in list(self.muted_users.items()):
            if datetime.now() >= unmute_time:
                try:
                    await client.edit_permissions(self.default_group_id, user_id, send_messages=True)
                    self.muted_users.remove(user_id)
                    logger.info(f"Unmuted user {user_id}")
                except Exception as e:
                    logger.error(f"Error unmuting user {user_id}: {str(e)}") 