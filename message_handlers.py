import logging
from telethon import events
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageHandlers:
    def __init__(self, client, daily_password, target_group):
        self.client = client
        self.daily_password = daily_password
        self.target_group = target_group
        self.VERSION = "0.23.2"  # 更新版本号

    async def handle_new_member(self, event):
        """Handle new member event"""
        try:
            # 获取新成员信息
            new_member = event.new_participant
            if not new_member:
                return
            
            # 获取用户信息
            user = await event.get_input_chat()
            username = getattr(user, 'username', None) or 'User'
            
            # 构建欢迎消息
            welcome_message = (
                f"Welcome {username} to the group!\n\n"
                f"To maintain group order, new members are muted.\n"
                f"Today's unmute password is: {self.daily_password}\n\n"
                f"Please send the daily password to the bot in private chat to unmute yourself."
            )
            
            # 发送欢迎消息
            await event.reply(welcome_message)
            
            # 禁言新成员
            try:
                await event.client.edit_permissions(
                    event.chat_id,
                    new_member,
                    until_date=None,
                    send_messages=False
                )
                logger.info(f"Successfully muted new member: {username}")
            except Exception as e:
                logger.error(f"Error muting new member: {e}")
            
        except Exception as e:
            logger.error(f"Error handling new member: {e}")

    async def handle_private_message(self, event):
        """Handle private messages"""
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
                        send_games=True
                    )
                    logger.info(f"Successfully unmuted user {user_id}")
                    await event.reply("密码正确！您的禁言已解除。")
                else:
                    await event.reply("密码正确，但群组ID未设置，请联系管理员。")
            else:
                await event.reply("密码错误，请重试。")
                
        except Exception as e:
            logger.error(f"Error handling private message: {str(e)}")

    async def handle_command(self, event):
        """Handle command messages"""
        try:
            message_text = event.message.text
            sender = await event.get_sender()
            username = sender.username if sender else "user"
            
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
                    "/account - Account management\n"
                    "/version - Show bot version"
                )
                await event.reply(help_text)
            elif message_text.lower() == '/pass':
                if event.is_private:
                    await event.reply(f"今日密码：{self.daily_password}")
                else:
                    await event.reply("请私聊机器人获取密码。")
            elif message_text.lower() == '/version':
                await event.reply(f"Bot version: {self.VERSION}")
            else:
                await event.reply(f"Hi {username}, you invoke function: {message_text[1:]}")
                
        except Exception as e:
            logger.error(f"Error handling command: {str(e)}")

    async def handle_mention(self, event):
        """Handle @ mentions"""
        try:
            sender = await event.get_sender()
            username = sender.username if sender else "user"
            message_text = event.message.text
            
            await event.reply(f"Hi, dear {username}, I got your message: {message_text}")
            
        except Exception as e:
            logger.error(f"Error handling mention: {str(e)}")

    async def handle_message(self, event):
        """Handle all messages"""
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
                await self.handle_mention(event)
                return
            
            # 处理命令
            if message_text.startswith('/'):
                await self.handle_command(event)
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def send_online_message(self):
        """Send online message to the group"""
        try:
            if self.target_group:
                message = (
                    f"🤖 Bot is now online!\n\n"
                    f"今日新用户解禁密码是：{self.daily_password}\n"
                    "新用户加入后将被禁言，请私聊机器人发送密码以解除禁言。"
                )
                await self.client.send_message(self.target_group, message)
                logger.info("Online message sent successfully")
        except Exception as e:
            logger.error(f"Error sending online message: {str(e)}") 