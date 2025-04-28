import logging
from telethon import events
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

def is_message_to_me(message, me):
    """检查消息是否@了机器人"""
    if not message or not me:
        return False
    
    # 检查消息文本中是否包含@用户名
    if hasattr(message, 'text') and message.text:
        if f"@{me.username}" in message.text:
            return True
    
    # 检查消息是否直接提及了机器人
    if hasattr(message, 'mentioned') and message.mentioned:
        return True
    
    return False

class MessageHandlers:
    def __init__(self, client, daily_password, target_group):
        self.client = client
        self.daily_password = daily_password
        self.target_group = target_group
        self.VERSION = "0.25.00"  # 更新版本号

    async def handle_new_member(self, event):
        """处理新成员加入事件"""
        try:
            new_member = event.user
            if not new_member:
                logger.warning("No new member found in event")
                return
            
            chat = await event.get_chat()
            logger.info(f"新成员 {new_member.first_name} (ID: {new_member.id}) 加入群组 {chat.title}")
            
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
                logger.info(f"成功禁言新成员 {new_member.first_name}")
                
                # 发送欢迎消息
                welcome_message = (
                    f"欢迎 {new_member.first_name} 加入群组!\n"
                    "为了维护群组秩序，新成员已被自动禁言。\n"
                    f"今日密码是: {self.daily_password}\n"
                    "请私聊机器人发送密码来解除禁言。"
                )
                await event.reply(welcome_message)
                logger.info(f"已发送欢迎消息给 {new_member.first_name}")
                
            except Exception as e:
                logger.error(f"禁言新成员时出错: {str(e)}")
                
        except Exception as e:
            logger.error(f"处理新成员时出错: {str(e)}")

    async def handle_command(self, event, command):
        """处理命令消息"""
        try:
            sender = await event.get_sender()
            username = sender.first_name if sender else "user"
            
            if command.lower() == '/pass':
                # 在任何场景都直接回复当日密码
                await event.reply(f"今日密码: {self.daily_password}")
                logger.info(f"已回复密码给用户 {username}")
            elif command.lower() == '/help':
                await self.handle_help_command(event)
            elif command.lower() == '/version':
                await event.reply(f"机器人版本: {self.VERSION}")
            else:
                await event.reply(f"您好 {username}, 此版本只支持 /pass、/help 和 /version 命令")
                
        except Exception as e:
            logger.error(f"处理命令时出错: {str(e)}")
    
    async def handle_help_command(self, event):
        """处理 /help 命令，显示帮助信息"""
        help_text = (
            "可用命令:\n"
            "/help - 显示此帮助信息\n"
            "/pass - 获取今日密码\n"
            "/version - 显示机器人版本"
        )
        await event.reply(help_text)

    async def handle_mention(self, event):
        """处理 @ 提及消息"""
        try:
            sender = await event.get_sender()
            username = sender.first_name if sender else "user"
            message_text = event.message.text
            
            await event.reply(f"您好 {username}，我已收到您的消息: {message_text}")
            
        except Exception as e:
            logger.error(f"处理@提及时出错: {str(e)}")

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
                        await event.reply("密码正确！您已被解除禁言。")
                        logger.info(f"成功解禁用户 {sender.first_name}")
                    except Exception as e:
                        logger.error(f"解禁用户时出错: {str(e)}")
                        await event.reply("解禁失败，请联系管理员。")
                else:
                    logger.error("未设置目标群组，无法解禁用户")
                    await event.reply("未设置目标群组，无法解禁。请联系管理员。")
            else:
                await event.reply(f"您好，如果您是新用户，请发送今日密码来解除禁言。\n今日密码可在群内通过 /pass 命令获取。")
                
        except Exception as e:
            logger.error(f"处理私聊消息时出错: {str(e)}")

    async def handle_chat_action(self, event):
        """处理群组事件"""
        try:
            # 如果是新成员加入
            if event.user_joined or event.user_added:
                await self.handle_new_member(event)
        except Exception as e:
            logger.error(f"处理群组事件时出错: {str(e)}")

    async def handle_message(self, event):
        """处理来自群组的消息"""
        try:
            message = event.message
            text = message.text if hasattr(message, 'text') else ''
            
            # 记录消息
            logger.info(f"收到群组消息: {text[:30]}... 来自用户ID: {message.sender_id}")
            
            # 处理命令
            if text.startswith('/'):
                logger.info(f"检测到命令: {text}")
                
                # 分离命令和参数
                parts = text.split(' ', 1)
                command = parts[0][1:].lower()  # 去掉/并转为小写
                args = parts[1] if len(parts) > 1 else ''
                
                # 处理pass命令
                if command == 'pass':
                    logger.info("收到每日密码请求，发送当前密码")
                    
                    # 发送每日密码
                    reply_text = f"今日密码是: {self.daily_password}\n新成员需要私聊该密码给机器人解除发言限制。"
                    await self.client.send_message(
                        event.chat_id,
                        reply_text,
                        reply_to=message.id
                    )
                    logger.info(f"已发送每日密码到群组, 响应用户: {message.sender_id}")
                    return
                    
                # 处理其他命令...
                
                # 处理版本命令
                elif command == 'version':
                    from web_service import VERSION
                    await self.client.send_message(
                        event.chat_id,
                        f"当前版本: {VERSION}", 
                        reply_to=message.id
                    )
                    logger.info(f"已发送版本信息到群组")
                    return
                    
            # 处理@bot的消息
            if is_message_to_me(message, self.client.get_me()):
                await self.handle_mentioned_message(event)
                return
                
        except Exception as e:
            logger.error(f"处理群组消息时出错: {e}")
            logger.error(traceback.format_exc())

    async def send_online_message(self):
        """发送上线消息"""
        try:
            if self.target_group:
                message = f"机器人已上线！\n版本: {self.VERSION}\n今日密码: {self.daily_password}\n新用户请私聊机器人发送密码解除禁言。"
                await self.client.send_message(self.target_group, message)
                logger.info("已发送上线消息")
            else:
                logger.warning("未设置目标群组，跳过发送上线消息")
        except Exception as e:
            logger.error(f"发送上线消息时出错: {str(e)}")
            
    def generate_random_message(self):
        """生成随机提醒消息"""
        return f"每日提醒: 新用户需要私聊机器人发送密码才能解除禁言。今日密码: {self.daily_password}"

    async def handle_mentioned_message(self, event):
        """处理@bot的消息"""
        try:
            message = event.message
            sender = await event.get_sender()
            username = sender.first_name if sender else "用户"
            
            # 提取消息文本
            text = message.text if hasattr(message, 'text') else ''
            
            # 记录@消息
            logger.info(f"收到@消息: {text[:30]}... 来自用户: {username}")
            
            # 回复用户
            reply_text = f"您好，{username}！我已收到您的消息：{text}"
            await self.client.send_message(
                event.chat_id,
                reply_text,
                reply_to=message.id
            )
            logger.info(f"已回复@消息给用户: {username}")
            
        except Exception as e:
            logger.error(f"处理@消息时出错: {e}")
            logger.error(traceback.format_exc()) 