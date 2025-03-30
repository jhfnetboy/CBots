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
        self.target_group = os.getenv('TELEGRAM_GROUP')  # 修改为 TELEGRAM_GROUP
        self.client = None
        self.muted_users = set()  # 记录被禁言的用户ID
        self.daily_password = self.generate_password()  # 生成每日密码
        self.message_handlers = None
        self.group_entity = None  # 缓存群组实体
        self.is_running = False  # 添加运行状态标志
        logger.info("TelegramCore initialized")

    def generate_password(self):
        """生成随机密码"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(8))

    async def get_group_entity(self, target):
        """获取群组实体"""
        try:
            if not self.group_entity and target:
                self.group_entity = await self.client.get_entity(target)
                logger.info(f"Got group entity: {self.group_entity.title} (ID: {self.group_entity.id})")
            return self.group_entity
        except Exception as e:
            logger.error(f"Error getting group entity: {str(e)}")
            return None

    async def start(self):
        """Start the Telegram core service"""
        try:
            logger.info("Starting Telegram core service...")
            
            # 检查必需的环境变量
            missing_vars = []
            if not self.api_id:
                missing_vars.append('TELEGRAM_API_ID')
                logger.debug(f"TELEGRAM_API_ID: {self.api_id}")
            if not self.api_hash:
                missing_vars.append('TELEGRAM_API_HASH')
                logger.debug(f"TELEGRAM_API_HASH: {self.api_hash}")
            if not self.bot_token:
                missing_vars.append('TELEGRAM_BOT_TOKEN')
                logger.debug(f"TELEGRAM_BOT_TOKEN: {self.bot_token}")
                
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
                
            session_file = "telegram_core_session"
            self.client = TelegramClient(session_file, self.api_id, self.api_hash)
            
            await self.client.start(bot_token=self.bot_token)
            logger.info("Telegram client started successfully")
            
            # 获取群组实体
            if self.target_group:
                await self.get_group_entity(self.target_group)
            
            # 初始化消息处理器
            self.message_handlers = MessageHandlers(
                client=self.client,
                daily_password=self.daily_password,
                target_group=self.target_group
            )
            logger.info("Message handlers initialized")
                
            # 设置事件处理器
            self.setup_handlers()
            
            # 设置运行状态
            self.is_running = True
            logger.info(f"Telegram core service started successfully - is_running: {self.is_running}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Telegram core service: {e}", exc_info=True)
            self.is_running = False
            return False

    def setup_handlers(self):
        """Set up event handlers"""
        try:
            # 注册新成员处理器
            @self.client.on(events.ChatAction)
            async def new_member_handler(event):
                if event.user_joined:
                    await self.message_handlers.handle_new_member(event)

            # 注册私聊消息处理器
            @self.client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
            async def private_message_handler(event):
                await self.message_handlers.handle_private_message(event)

            # 注册群组消息处理器（排除私聊消息）
            @self.client.on(events.NewMessage(incoming=True, func=lambda e: not e.is_private))
            async def group_message_handler(event):
                await self.message_handlers.handle_message(event)

            logger.info("Event handlers set up successfully")
        except Exception as e:
            logger.error(f"Error setting up event handlers: {e}", exc_info=True)
            raise

    async def send_message(self, message: str, channel: str = None, topic_id: int = None):
        """发送消息到 Telegram"""
        try:
            if not self.client:
                logger.error("Telegram client not initialized")
                raise Exception("Telegram client not initialized")
            
            logger.info(f"Attempting to send message: {message}")
            
            # 如果没有指定频道，使用默认群组
            target = channel if channel else self.target_group
            
            # 获取群组实体
            logger.info(f"Attempting to get entity for: {target}")
            group = await self.get_group_entity(target)
            logger.info(f"Found group: {group.title} (ID: {group.id})")
            
            # 发送消息
            if topic_id:
                logger.info(f"Sending message to topic {topic_id}")
                response = await self.client.send_message(
                    group,
                    message,
                    reply_to=topic_id
                )
            else:
                response = await self.client.send_message(
                    group,
                    message
                )
            
            logger.info(f"Message sent successfully! Message ID: {response.id}")
            return response.id
        
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

    async def stop(self):
        """Stop the Telegram core service"""
        try:
            if self.client:
                await self.client.disconnect()
            self.is_running = False  # 设置运行状态
            logger.info("Telegram core service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Telegram core service: {e}", exc_info=True)
            raise 