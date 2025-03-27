import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self):
        self.muted_users = set()  # 改为集合，只记录被禁言的用户ID
        self.default_group_id = os.getenv('TELEGRAM_DEFAULT_GROUP')  # 使用环境变量中的群组ID

    async def send_online_message(self, client):
        """Send online message to the group"""
        try:
            # Get group ID from environment variable
            group_id = os.getenv('TELEGRAM_GROUP')
            if not group_id:
                logger.error("TELEGRAM_GROUP not found in environment variables")
                return
                
            # Send online message
            await client.send_message(group_id, "🤖 Bot is now online!")
            logger.info("Online message sent successfully")
        except Exception as e:
            logger.error(f"Error sending online message: {str(e)}")

    async def send_daily_password(self, client):
        """Send daily password to default group"""
        try:
            if not self.default_group_id:
                logger.error("TELEGRAM_DEFAULT_GROUP not set in environment variables")
                return
                
            password = os.getenv('DAILY_PASSWORD', '')
            await client.send_message(self.default_group_id, f"今日密码：{password}")
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
        """Handle new member joins"""
        try:
            if event.user_joined:
                user_id = event.user_id
                # Mute user in default group
                await client.edit_permissions(self.default_group_id, user_id, send_messages=False)
                logger.info(f"Muted user {user_id} in group {self.default_group_id}")
                
                # Add user to muted users set
                self.muted_users.add(user_id)
                
                # Send welcome message
                await event.reply(f"欢迎新成员！请在24小时内私聊机器人发送每日密码以解除禁言。")
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
                if message_text == os.getenv('DAILY_PASSWORD', ''):
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