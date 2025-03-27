import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self):
        self.muted_users = {}
        self.default_group_id = int(os.getenv('DEFAULT_GROUP_ID', 1))

    async def send_online_message(self, client):
        """Send online message to default group"""
        try:
            message = "Hi，COS72 Bot is online now。/help了解更多。"
            await client.send_message(self.default_group_id, message)
            logger.info(f"Sent online message to group {self.default_group_id}")
        except Exception as e:
            logger.error(f"Error sending online message: {str(e)}")

    async def send_daily_password(self, client):
        """Send daily password to default group"""
        try:
            password = os.getenv('DAILY_PASSWORD', '')
            await client.send_message(self.default_group_id, f"今日密码：{password}")
            logger.info(f"Sent daily password to group {self.default_group_id}")
        except Exception as e:
            logger.error(f"Error sending daily password: {str(e)}")

    async def handle_message(self, event, command_manager):
        """Handle new messages"""
        try:
            # Log the message
            logger.info(f"Received message from {event.sender_id}: {event.message.text}")
            
            # Check if user is muted
            if event.sender_id in self.muted_users:
                await event.reply("您当前处于禁言状态，请私聊机器人发送每日密码以解除禁言。")
                return
            
            # Get response from command manager
            response = await command_manager.handle_message(event.message.text)
            
            # Send response back to user
            await event.reply(response)
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await event.reply("Sorry, there was an error processing your message.")

    async def handle_new_member(self, event, client):
        """Handle new member joins"""
        try:
            if event.user_joined:
                user_id = event.user_id
                # Mute user in default group
                await client.edit_permissions(self.default_group_id, user_id, send_messages=False)
                logger.info(f"Muted user {user_id} in group {self.default_group_id}")
                
                # Store unmute time (24 hours from now)
                self.muted_users[user_id] = datetime.now() + timedelta(hours=24)
                
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
                    
                    # Update unmute time to 1 hour from now
                    self.muted_users[user_id] = datetime.now() + timedelta(hours=1)
                    
                    await event.reply("密码正确！您的禁言将在1小时后解除。")
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
                    del self.muted_users[user_id]
                    logger.info(f"Unmuted user {user_id}")
                except Exception as e:
                    logger.error(f"Error unmuting user {user_id}: {str(e)}") 