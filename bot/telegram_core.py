import logging
import os
from telethon import TelegramClient, events
from telethon.tl.types import Message
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv
import random
import string
from message_handlers import MessageHandlers
from telethon.sessions import StringSession

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
        self.target_group = os.getenv('TELEGRAM_GROUP')
        self.client = None
        self.group_entity = None
        self.message_handlers = None
        self.is_running = False
        self.lock = asyncio.Lock()
        self._loop = None
        self.muted_users = set()  # 记录被禁言的用户ID
        self.daily_password = self.generate_password()  # 生成每日密码
        logger.info("TelegramCore initialized")

    def generate_password(self):
        """生成随机密码"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(8))

    async def get_group_entity(self):
        """获取群组实体"""
        try:
            if not self.group_entity:
                self.group_entity = await self.client.get_entity(self.target_group)
                logger.info(f"Got group entity: {self.group_entity.title} (ID: {self.group_entity.id})")
            return self.group_entity
        except Exception as e:
            logger.error(f"Error getting group entity: {str(e)}")
            return None

    async def start(self):
        """启动Telegram客户端"""
        try:
            if not self._loop:
                self._loop = asyncio.get_event_loop()
            
            self.client = TelegramClient(
                StringSession(),
                self.api_id,
                self.api_hash,
                loop=self._loop
            )
            
            await self.client.start(bot_token=self.bot_token)
            self.is_running = True
            
            # 获取并缓存群组实体
            await self.get_group_entity()
            
            # 初始化消息处理器
            self.message_handlers = MessageHandlers(self)
            
            # 设置事件处理器
            self.client.add_event_handler(
                self.message_handlers.handle_new_member,
                events.ChatAction
            )
            
            # 注册命令处理器
            @self.client.on(events.NewMessage(pattern='/hi'))
            async def hi_handler(event):
                await self.message_handlers.handle_hi_command(event)
            
            @self.client.on(events.NewMessage(pattern='/start'))
            async def start_handler(event):
                await self.message_handlers.handle_start_command(event)
            
            @self.client.on(events.NewMessage(pattern='/help'))
            async def help_handler(event):
                await self.message_handlers.handle_help_command(event)
            
            # 处理 @bot 消息
            @self.client.on(events.NewMessage(func=lambda e: e.mentioned))
            async def mention_handler(event):
                await self.message_handlers.handle_mention(event)
            
            # 处理私聊消息
            @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
            async def private_message_handler(event):
                await self.message_handlers.handle_private_message(event)
            
            # 发送上线消息
            await self.message_handlers.send_online_message()
            
            logger.info("Telegram service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Telegram service: {e}")
            return False
            
    async def stop(self):
        """停止Telegram客户端"""
        try:
            if self.client:
                await self.client.disconnect()
            self.is_running = False
            logger.info("Telegram service stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping Telegram service: {e}")
            return False
            
    async def send_message(self, message: str, channel: str = None, topic_id: int = None, scheduled_time: str = None) -> dict:
        """发送消息到指定频道或群组"""
        try:
            if not self.client or not self.is_running:
                return {"error": "Telegram service is not running"}
                
            logger.info(f"Attempting to send message: {message}")
            
            # 使用传入的频道或默认群组
            target = channel if channel else self.target_group
            if not target:
                return {"error": "No target channel or group specified"}
                
            # 获取目标实体
            entity = await self.get_group_entity()
            if not entity:
                return {"error": f"Could not find entity for {target}"}
                
            # 如果有定时发送时间
            if scheduled_time:
                scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                now = datetime.utcnow()
                
                if scheduled_datetime <= now:
                    return {"error": "Scheduled time must be in the future"}
                    
                # 计算延迟时间
                delay = (scheduled_datetime - now).total_seconds()
                
                # 创建后台任务发送消息
                asyncio.create_task(self._send_scheduled_message(entity, message, delay, topic_id))
                
                # 计算天、小时、分钟
                days = int(delay // (24 * 3600))
                hours = int((delay % (24 * 3600)) // 3600)
                minutes = int((delay % 3600) // 60)
                
                # 构建提示信息
                timing_info = []
                if days > 0:
                    timing_info.append(f"{days} days ")
                if hours > 0:
                    timing_info.append(f"{hours} hours ")
                if minutes > 0:
                    timing_info.append(f"{minutes} minutes")
                    
                timing_str = "".join(timing_info).strip()
                
                return {
                    "status": "scheduled",
                    "message": f"Message scheduled successfully. Will be sent in {timing_str}",
                    "scheduled_time": scheduled_datetime.isoformat()
                }
            
            # 立即发送消息
            async with self.lock:
                response = await self.client.send_message(
                    entity,
                    message,
                    reply_to=topic_id if topic_id else None
                )
                
            return {
                "status": "success",
                "message": "Message sent successfully",
                "message_id": response.id
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return {"error": str(e)}
            
    async def _send_scheduled_message(self, entity, message: str, delay: float, topic_id: int = None):
        """后台任务：发送定时消息"""
        try:
            await asyncio.sleep(delay)
            
            async with self.lock:
                response = await self.client.send_message(
                    entity,
                    message,
                    reply_to=topic_id if topic_id else None
                )
                
            logger.info(f"Scheduled message sent successfully. Message ID: {response.id}")
            
        except Exception as e:
            logger.error(f"Error sending scheduled message: {e}", exc_info=True)

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
                if self.message_handlers:
                    self.message_handlers.daily_password = self.daily_password
                
                # 发送每日密码到群组
                if self.group_entity:
                    await self.send_message(
                        self.group_entity,
                        f"今日新用户解禁密码是：{self.daily_password}"
                    )
                
            except Exception as e:
                logger.error(f"Error in daily verification task: {e}", exc_info=True)
                await asyncio.sleep(60)  # 出错后等待1分钟再试 