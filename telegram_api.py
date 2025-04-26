import logging
import asyncio
from datetime import datetime, timedelta
from telegram_core import TelegramCore
from image_sender import ImageSender
import re

logger = logging.getLogger(__name__)

class TelegramAPI:
    def __init__(self, core: TelegramCore = None):
        self.core = core or TelegramCore()
        self.is_running = False

    async def send_message(self, message, channel=None, topic_id=None, scheduled_time=None, image_data=None, image_url=None, group_name=None, image=None, reply_to=None):
        """
        Send a message to a Telegram group/channel
        
        Args:
            message (str): Message text to send
            channel (str, optional): Channel/Group name
            topic_id (int, optional): Topic ID for forum channels
            scheduled_time (str, optional): Time to schedule the message (ISO format)
            image_data (str, optional): Base64 encoded image data
            image_url (str, optional): URL to an image
            group_name (str, optional): Legacy parameter for group name (alias for channel)
            image (str, optional): Legacy parameter for image (alias for image_data or image_url)
            reply_to (int, optional): Message ID to reply to
            
        Returns:
            dict: Result information
        """
        try:
            # 向后兼容：处理参数别名
            _group_name = group_name or channel or ''
            _image = image or image_data or image_url or None
            _schedule_time = scheduled_time or None
            
            # Log the parameters
            logger.info(f"Send message request - group: {_group_name}, topic_id: {topic_id}")
            logger.info(f"Message length: {len(message) if message else 0}")
            logger.info(f"With image: {bool(_image)}, reply_to: {reply_to}, schedule: {_schedule_time}")
            
            # 添加对话题(topic)的支持
            if topic_id and _group_name:
                _group_name = f"{_group_name}/{topic_id}"
                logger.info(f"Formatting group name with topic: {_group_name}")
            
            # Check service status
            if not self.connected:
                status = await self.connect()
                if not status:
                    logger.error("Could not connect to Telegram")
                    return {"success": False, "error": "Could not connect to Telegram"}
            
            # Process scheduled time if provided
            schedule_datetime = None
            if _schedule_time:
                try:
                    # 处理可能的'Z'后缀
                    if isinstance(_schedule_time, str) and _schedule_time.endswith('Z'):
                        _schedule_time = _schedule_time.replace('Z', '+00:00')
                    
                    schedule_datetime = datetime.fromisoformat(_schedule_time)
                    now = datetime.now()
                    
                    # Check if the scheduled time is in the past
                    if schedule_datetime < now:
                        logger.error(f"Scheduled time is in the past: {_schedule_time}")
                        return {"success": False, "error": "Scheduled time must be in the future"}
                        
                    # Check if the scheduled time is too far in the future (more than 365 days)
                    if schedule_datetime > now + timedelta(days=365):
                        logger.error(f"Scheduled time is too far in the future: {_schedule_time}")
                        return {"success": False, "error": "Scheduled time cannot be more than 365 days in the future"}
                        
                    logger.info(f"Message scheduled for: {schedule_datetime.isoformat()}")
                    
                except ValueError as e:
                    logger.error(f"Invalid schedule time format: {e}")
                    return {"success": False, "error": f"Invalid schedule time format: {e}"}
            
            # Process image if provided
            image_file = None
            if _image:
                logger.info("Processing image data...")
                
                # Check if it's base64 data
                if isinstance(_image, str) and _image.startswith('data:image/'):
                    logger.info("Processing base64 image data")
                    image_file = ImageSender.process_base64_image(_image)
                    if not image_file:
                        logger.error("Failed to process base64 image")
                        return {"success": False, "error": "Failed to process base64 image"}
                
                # Check if it's a markdown image ![alt](url)
                elif isinstance(_image, str) and re.match(r'!\[.*?\]\((.*?)\)', _image):
                    url_match = re.match(r'!\[.*?\]\((.*?)\)', _image)
                    if url_match:
                        image_url = url_match.group(1)
                        logger.info(f"Detected Markdown image reference, downloading from URL: {image_url}")
                        image_file = ImageSender.download_image_from_url(image_url)
                        if not image_file:
                            logger.error(f"Failed to download image from URL: {image_url}")
                            return {"success": False, "error": f"Failed to download image from URL: {image_url}"}
                
                # Check if it's a URL
                elif isinstance(_image, str) and (
                    _image.startswith('http://') or _image.startswith('https://')
                ):
                    logger.info(f"Downloading image from URL: {_image}")
                    image_file = ImageSender.download_image_from_url(_image)
                    if not image_file:
                        logger.error(f"Failed to download image from URL: {_image}")
                        return {"success": False, "error": f"Failed to download image from URL: {_image}"}
                
                # Check if it's a file path
                elif isinstance(_image, str) and ImageSender.is_valid_image_path(_image):
                    logger.info(f"Using image from file path: {_image}")
                    image_file = _image
                
                # Invalid image input
                else:
                    logger.error(f"Invalid image input: {type(_image)}")
                    return {"success": False, "error": "Invalid image input"}
            
            # Send the message
            logger.info(f"Calling core.send_message with parameters: channel_name={_group_name}, image_path={image_file.name if image_file and hasattr(image_file, 'name') else image_file}")
            result = await self.core.send_message(
                message=message,
                channel_name=_group_name,
                image_path=image_file,
                topic_id=reply_to
            )
            
            # 处理返回结果
            if isinstance(result, dict) and "status" in result and result["status"] == "success":
                msg_id = result.get("message_id")
                logger.info(f"Message sent successfully, ID: {msg_id}")
                return {
                    "success": True,
                    "message_id": msg_id,
                    "group": _group_name,
                    "scheduled": bool(_schedule_time),
                    "status": "scheduled" if bool(_schedule_time) else "sent"
                }
            elif isinstance(result, dict) and "error" in result:
                error_msg = result["error"]
                logger.error(f"Error from core: {error_msg}")
                return {"success": False, "error": error_msg}
            else:
                logger.info(f"Message sent with unknown result: {result}")
                return {
                    "success": True,
                    "result": result,
                    "group": _group_name,
                    "scheduled": bool(_schedule_time),
                    "status": "scheduled" if bool(_schedule_time) else "sent"
                }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error sending message: {error_msg}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": error_msg}

    async def get_status(self):
        """获取 Telegram 服务状态"""
        try:
            if not self.core.is_running:
                return {"status": "stopped"}
            
            return {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "daily_password": self.core.daily_password
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {"error": str(e)}

    async def start(self):
        """启动 Telegram API 服务"""
        try:
            # 确保 core 已启动
            if not self.core.is_running:
                result = await self.core.start()
                if not result:
                    logger.error("Failed to start Telegram core service")
                    return False
            
            self.is_running = True
            logger.info("Telegram API service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Telegram API service: {str(e)}")
            self.is_running = False
            return False

    async def stop(self):
        """停止 Telegram API 服务"""
        try:
            await self.core.stop()
            self.is_running = False
            return {"status": "success", "message": "Telegram API service stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping Telegram API service: {str(e)}")
            return {"error": str(e)}

    async def connect(self):
        """连接到Telegram服务，适用于PythonAnywhere环境"""
        try:
            import os
            import traceback
            from telethon import TelegramClient
            
            # 从环境变量获取凭证
            api_id = os.environ.get('TELEGRAM_API_ID')
            api_hash = os.environ.get('TELEGRAM_API_HASH')
            bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
            
            # 检查必要凭证
            if not all([api_id, api_hash, bot_token]):
                logger.error("Missing required credentials")
                return False
                
            # 创建session路径
            session_path = "telegram_session"
            
            # 创建客户端并连接
            self.client = TelegramClient(
                session_path,
                api_id=int(api_id),
                api_hash=api_hash
            )
            
            await self.client.start(bot_token=bot_token)
            
            # 检查连接状态
            self.connected = self.client.is_connected()
            logger.info(f"Telegram API连接状态: {self.connected}")
            
            # 如果有现有核心服务，更新其客户端
            if hasattr(self, 'core') and self.core:
                self.core.client = self.client
                logger.info("更新了核心服务的客户端引用")
                
            return self.connected
            
        except Exception as e:
            logger.error(f"连接到Telegram出错: {e}")
            logger.error(traceback.format_exc())
            self.connected = False
            return False
    
    async def disconnect(self):
        """断开Telegram连接，适用于PythonAnywhere环境"""
        try:
            if hasattr(self, 'client') and self.client:
                await self.client.disconnect()
                logger.info("成功断开Telegram连接")
            
            self.connected = False
            return True
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")
            return False
            
    @property
    def connected(self):
        """检查是否已连接到Telegram"""
        if hasattr(self, '_connected'):
            return self._connected
        return False
        
    @connected.setter
    def connected(self, value):
        """设置连接状态"""
        self._connected = value 