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
        """Handle new member joined event"""
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
                    send_games=False
                )
                logger.info(f"Successfully muted new member {new_member.first_name} permanently")
                
                # 发送欢迎消息
                welcome_message = (
                    f"欢迎 {new_member.first_name} 加入群组！\n"
                    "为了维护群组秩序，新成员将被禁言。\n"
                    f"今日解禁密码是：{self.daily_password}\n"
                    "请私聊机器人并发送每日密码以解除禁言。"
                )
                await event.reply(welcome_message)
                logger.info(f"Sent welcome message to {new_member.first_name}")
                
            except Exception as e:
                logger.error(f"Error muting new member: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error handling new member: {str(e)}")

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