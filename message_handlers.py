import logging
from telethon import events
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageHandlers:
    def __init__(self, client, daily_password, target_group):
        self.client = client
        self.daily_password = daily_password
        self.target_group = target_group
        self.VERSION = "0.23.50"  # 独立的版本号定义

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
                    f"Welcome {new_member.first_name} to the group!\n"
                    "To maintain group order, new members are muted.\n"
                    f"Today's password is: {self.daily_password}\n"
                    "Please send the password to the bot in private chat to unmute."
                )
                await event.reply(welcome_message)
                logger.info(f"Sent welcome message to {new_member.first_name}")
                
            except Exception as e:
                logger.error(f"Error muting new member: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error handling new member: {str(e)}")

    async def handle_command(self, event, command):
        """处理命令消息"""
        try:
            sender = await event.get_sender()
            username = sender.first_name if sender else "user"
            is_private = event.is_private
            
            if command.lower() == '/hi':
                await self.handle_hi_command(event)
            elif command.lower() == '/help':
                await self.handle_help_command(event)
            elif command.lower() == '/pass':
                # 在任何场景都直接回复当日密码
                await event.reply(f"Today's password: {self.daily_password}")
            elif command.lower() == '/version':
                await self.handle_version_command(event)
            elif command.lower() == '/price':
                await self.handle_price_command(event)
            elif command.lower() == '/event':
                await self.handle_event_command(event)
            elif command.lower() == '/task':
                await self.handle_task_command(event)
            elif command.lower() == '/pnts':
                await self.handle_pnts_command(event)
            elif command.lower() == '/account':
                await self.handle_account_command(event)
            else:
                await event.reply(f"Hi {username}, you invoke function: {command[1:]}")
                
        except Exception as e:
            logger.error(f"Error handling command: {str(e)}")
    
    async def handle_help_command(self, event):
        """处理 /help 命令，显示帮助信息"""
        help_text = (
            "Available commands:\n"
            "/help - Show this help message in public\n"
            "/hi - Say hello in public\n"
            "/price - Show price information in public group\n"
            "/event - Show events list in public group\n"
            "/task - Show task list in public group\n"
            "/PNTs - Show your PNTs information in private chat\n"
            "/account - Show account information in private chat\n"
            "/version - Show bot version in public"
        )
        await event.reply(help_text)
    
    async def handle_hi_command(self, event):
        """处理 /hi 命令，打招呼"""
        await event.reply("Hi, my friends, this is COS72 Bot.")
    
    async def handle_version_command(self, event):
        """处理 /version 命令，显示版本信息"""
        await event.reply(f"Bot version: {self.VERSION}")
    
    async def handle_price_command(self, event):
        """处理 /price 命令，显示价格信息"""
        await event.reply("Current price information: $1.23 (+5.2%)")
    
    async def handle_event_command(self, event):
        """处理 /event 命令，显示事件列表"""
        events_text = (
            "Upcoming events:\n"
            "1. Community Call - April 5th, 2025\n"
            "2. Hackathon - April 10-12, 2025\n"
            "3. AMA Session - April 15th, 2025"
        )
        await event.reply(events_text)
    
    async def handle_task_command(self, event):
        """处理 /task 命令，显示任务列表"""
        tasks_text = (
            "Current tasks:\n"
            "1. Community Testing - 100 PNTs\n"
            "2. Bug Reporting - 50 PNTs\n"
            "3. Documentation Review - 30 PNTs"
        )
        await event.reply(tasks_text)
    
    async def handle_pnts_command(self, event):
        """处理 /pnts 命令，显示 PNTs 信息"""
        if event.is_private:
            await event.reply("Your PNTs balance: 250 PNTs\nRank: Silver Member")
        else:
            await event.reply("Please send the /PNTs command in a private message to check your PNTs information.")
    
    async def handle_account_command(self, event):
        """处理 /account 命令，显示账户信息"""
        if event.is_private:
            account_info = (
                "Account Information:\n"
                f"Name: {event.sender.first_name}\n"
                f"ID: {event.sender.id}\n"
                "Membership: Active since January 2025\n"
                "PNTs: 250\n"
                "Rank: Silver Member"
            )
            await event.reply(account_info)
        else:
            await event.reply("Please send the /account command in a private message to check your account information.")

    async def handle_mention(self, event):
        """处理 @ 提及消息"""
        try:
            sender = await event.get_sender()
            username = sender.first_name if sender else "user"
            message_text = event.message.text
            
            await event.reply(f"Hi, dear {username}, I got your message: {message_text}")
            
        except Exception as e:
            logger.error(f"Error handling mention: {str(e)}")

    async def handle_private_message(self, event):
        """处理私聊消息"""
        try:
            sender = await event.get_sender()
            message_text = event.message.text
            
            # 处理命令消息
            if message_text.startswith('/'):
                await self.handle_command(event, message_text)
                return
                
            # 处理普通消息（密码验证等）
            # 检查是否是解禁密码
            if message_text == self.daily_password:
                # 直接使用目标群组
                if self.target_group:
                    try:
                        # 解除禁言
                        await self.client.edit_permissions(
                            self.target_group,
                            sender.id,
                            until_date=None,
                            send_messages=True,
                            send_media=True,
                            send_stickers=True,
                            send_gifs=True,
                            send_games=True
                        )
                        await event.reply("Password correct! You have been unmuted.")
                        logger.info(f"Successfully unmuted user {sender.first_name} in group {self.target_group}")
                    except Exception as e:
                        logger.error(f"Error unmuting user in group {self.target_group}: {str(e)}")
                        await event.reply("Failed to unmute, please contact admin.")
                else:
                    await event.reply("Target group not set, please contact admin.")
            else:
                await event.reply("Incorrect password, please try again.")
                
        except Exception as e:
            logger.error(f"Error handling private message: {str(e)}")

    async def handle_message(self, event):
        """处理所有消息"""
        try:
            # 获取消息信息
            message_text = event.message.text
            sender = await event.get_sender()
            username = sender.first_name if sender else "user"
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
                await self.handle_command(event, message_text)
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    async def send_online_message(self):
        """发送上线消息到群组"""
        try:
            if self.target_group:
                message = (
                    f"🤖 Bot is now online!\n\n"
                    f"Today's password is: {self.daily_password}\n"
                    "New members will be muted, please send the password to the bot in private chat to unmute."
                )
                await self.client.send_message(self.target_group, message)
                logger.info("Online message sent successfully")
        except Exception as e:
            logger.error(f"Error sending online message: {str(e)}") 