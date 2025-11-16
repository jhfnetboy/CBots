import logging
import os
from telethon import TelegramClient, events
from telethon.tl.types import Message, InputPeerChannel, PeerChannel
from telethon.errors import ChannelPrivateError
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv
import random
import string
from message_handlers import MessageHandlers
from io import BytesIO

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

    async def get_group_entity(self, group_name):
        """Get group entity by name"""
        try:
            if not self.client:
                logger.error("Client not initialized")
                return None
                
            logger.info(f"Attempting to get entity for: {group_name}")
            
            # 尝试将group_name解析为整数（频道ID）
            try:
                if isinstance(group_name, int) or (isinstance(group_name, str) and str(group_name).isdigit()):
                    # 如果是整数或纯数字，假设它是一个频道ID
                    channel_id = int(group_name)
                    logger.info(f"Processing numeric channel ID: {channel_id}")
                    # 尝试不同的方法获取实体
                    try:
                        # 方法1: 使用InputPeerChannel
                        peer = InputPeerChannel(channel_id=channel_id, access_hash=0)
                        entity = await self.client.get_entity(peer)
                        logger.info(f"Got channel entity by InputPeerChannel: {entity.title if hasattr(entity, 'title') else 'Unknown'} (ID: {entity.id})")
                        return entity
                    except Exception as e1:
                        logger.warning(f"Method 1 failed: {e1}")
                        try:
                            # 方法2: 使用PeerChannel
                            peer = PeerChannel(channel_id=channel_id)
                            entity = await self.client.get_entity(peer)
                            logger.info(f"Got channel entity by PeerChannel: {entity.title if hasattr(entity, 'title') else 'Unknown'} (ID: {entity.id})")
                            return entity
                        except Exception as e2:
                            logger.warning(f"Method 2 failed: {e2}")
                            try:
                                # 方法3: 直接使用ID
                                entity = await self.client.get_entity(channel_id)
                                logger.info(f"Got channel entity by direct ID: {entity.title if hasattr(entity, 'title') else 'Unknown'} (ID: {entity.id})")
                                return entity
                            except Exception as e3:
                                logger.error(f"All methods failed for numeric ID {channel_id}: {e3}")
                                raise
            except Exception as e:
                logger.warning(f"Failed to get entity as numeric ID, trying as username: {e}")
            
            # 如果不是数字ID或上面的尝试失败，使用普通方式获取
            group = await self.client.get_entity(group_name)
            logger.info(f"Got group entity: {group.title} (ID: {group.id})")
            return group
        except ChannelPrivateError:
            logger.error(f"Cannot access private channel: {group_name}. The bot must be a member of the channel.")
            return None
        except ValueError as e:
            logger.error(f"Error getting group entity: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting group entity: {e}")
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
                
            # 使用时间戳创建唯一的session文件名
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            session_file = f"sessions/telegram_session_{current_time}"
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

    async def send_message(self, message, channel_name=None, topic_id=None, image_path=None):
        """Send a message to the target group or channel"""
        try:
            # 日志输出参数
            logger.info(f"Attempting to send message: {message}")
            
            if not self.client:
                logger.error("Telegram client not initialized")
                return {"error": "Telegram client not initialized"}
                
            if not channel_name:
                # 使用默认群组
                channel_name = os.environ.get('TELEGRAM_GROUP')
                if not channel_name:
                    logger.error("No channel specified and TELEGRAM_GROUP not set in environment")
                    return {"error": "No channel specified"}
            
            # 获取群组实体
            logger.info(f"Attempting to get entity for: {channel_name}")
            group = await self.get_group_entity(channel_name)
            
            if not group:
                logger.error(f"Failed to get group entity for: {channel_name}")
                return {"error": f"Failed to get group entity for: {channel_name}"}
                
            # 记录找到的群组信息
            if hasattr(group, 'title'):
                logger.info(f"Found group: {group.title} (ID: {group.id})")
            else:
                logger.info(f"Found entity with ID: {group.id} (no title available)")
                
            if image_path:
                # 发送带图片的消息
                logger.info(f"Sending message with image to topic {topic_id}")
                if topic_id:
                    result = await self.client.send_message(
                        group,
                        message,
                        file=image_path,
                        reply_to=topic_id
                    )
                else:
                    result = await self.client.send_message(
                        group,
                        message,
                        file=image_path
                    )
            else:
                # 发送纯文本消息
                if topic_id:
                    logger.info(f"Sending text message to topic {topic_id}")
                    result = await self.client.send_message(
                        group,
                        message,
                        reply_to=topic_id
                    )
                else:
                    logger.info("Sending text message without topic")
                    result = await self.client.send_message(
                        group,
                        message
                    )
            
            logger.info(f"Message sent successfully! Message ID: {result.id}")
            return {"status": "success", "message": "Message sent successfully", "message_id": result.id}
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return {"error": str(e)}

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