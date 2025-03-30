import logging
import asyncio
from datetime import datetime
from telegram_core import TelegramCore

logger = logging.getLogger(__name__)

class TelegramAPI:
    def __init__(self, core: TelegramCore = None):
        self.core = core or TelegramCore()
        self.is_running = False

    async def send_message(self, message: str, channel: str = None, topic_id: int = None, scheduled_time: str = None, image_data: str = None, image_url: str = None):
        """发送消息到 Telegram"""
        try:
            # 检查服务状态
            logger.info(f"TelegramAPI.send_message called with params: message={message}, channel={channel}, topic_id={topic_id}, scheduled_time={scheduled_time}, has_image={bool(image_data)}, has_image_url={bool(image_url)}")
            logger.info(f"Checking service status - core.is_running: {self.core.is_running}, client: {self.core.client is not None}")
            
            if not self.core.client:
                logger.error("Telegram client is not initialized")
                return {"error": "Telegram client not initialized"}
            
            # 明确检查 scheduled_time 类型
            logger.info(f"scheduled_time type: {type(scheduled_time)}, value: {scheduled_time}")
            
            # 检查 scheduled_time 是否未定义或为空
            if scheduled_time is None or scheduled_time == "" or scheduled_time == "undefined" or scheduled_time == "null":
                # 直发消息
                logger.info(f"Sending immediate message to channel: {channel}, topic_id: {topic_id}, has image: {bool(image_data)}, has image URL: {bool(image_url)}")
                return await self._send_message_now(message, channel, topic_id, image_data, image_url)
            
            # 如果是定时发送，创建后台任务
            logger.info(f"Scheduling message for {scheduled_time}")
            asyncio.create_task(self._schedule_message(message, channel, topic_id, scheduled_time, image_data, image_url))
            return {
                "status": "scheduled",
                "message": "Message scheduled successfully",
                "scheduled_time": scheduled_time
            }
            
        except Exception as e:
            logger.error(f"Error in TelegramAPI.send_message: {str(e)}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return {"error": str(e)}

    async def _schedule_message(self, message: str, channel: str, topic_id: int, scheduled_time: str, image_data: str = None, image_url: str = None):
        """处理定时发送消息的后台任务"""
        try:
            # 解析计划时间
            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', ''))
            now = datetime.now()
            
            if scheduled_datetime <= now:
                logger.error("Scheduled time is in the past")
                return
            
            # 计算延迟时间
            delay = (scheduled_datetime - now).total_seconds()
            logger.info(f"Scheduling message for {scheduled_datetime} (delay: {delay}s)")
            
            # 等待到指定时间
            await asyncio.sleep(delay)
            
            # 添加定时信息到消息中
            formatted_time = scheduled_datetime.strftime('%Y-%m-%d %H:%M')
            enhanced_message = f"{message}\n\n[Scheduled message sent at {formatted_time}]"
            
            # 发送消息
            await self._send_message_now(enhanced_message, channel, topic_id, image_data, image_url)
            
        except Exception as e:
            logger.error(f"Error in scheduled message task: {str(e)}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")

    async def _send_message_now(self, message: str, channel: str, topic_id: int, image_data: str = None, image_url: str = None):
        """立即发送消息"""
        try:
            if image_data or image_url:
                # 处理图片
                import base64
                from io import BytesIO
                import time
                import aiohttp
                import re
                
                try:
                    image_file = None
                    
                    if image_data:
                        # 处理上传的Base64图片
                        content_type = image_data.split(';')[0].split(':')[1]
                        ext = content_type.split('/')[1]  # 获取文件格式 (如 jpeg, png)
                        file_name = f"image_{int(time.time())}.{ext}"  # 生成文件名
                        
                        image_bytes = base64.b64decode(image_data.split(',')[1])
                        image_file = BytesIO(image_bytes)
                        image_file.name = file_name  # 设置文件名
                        
                        logger.info(f"Sending uploaded image with filename: {file_name}, content-type: {content_type}")
                    
                    elif image_url:
                        # 处理 Markdown 格式的图片 URL
                        # 匹配 markdown 格式: ![alt text](https://example.com/image.jpg)
                        markdown_match = re.match(r'!\[(.*?)\]\((.*?)\)', image_url)
                        if markdown_match:
                            # 提取真正的 URL
                            image_url = markdown_match.group(2)
                            logger.info(f"Extracted URL from Markdown format: {image_url}")
                        
                        # 提取文件扩展名
                        ext = image_url.split('.')[-1].lower()
                        if '?' in ext:  # 处理URL中可能的查询参数
                            ext = ext.split('?')[0]
                        
                        # 如果扩展名不是常见图片格式，默认使用jpg
                        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                            ext = 'jpg'
                            
                        file_name = f"image_{int(time.time())}.{ext}"
                        
                        # 下载图片
                        async with aiohttp.ClientSession() as session:
                            logger.info(f"Downloading image from URL: {image_url}")
                            async with session.get(image_url) as response:
                                if response.status == 200:
                                    image_bytes = await response.read()
                                    image_file = BytesIO(image_bytes)
                                    image_file.name = file_name
                                    logger.info(f"Successfully downloaded image, size: {len(image_bytes)} bytes")
                                else:
                                    logger.error(f"Failed to download image, status code: {response.status}")
                                    return {"error": f"Failed to download image from URL, status code: {response.status}"}
                    
                    # 发送图片和文本
                    message_id = await self.core.send_message(
                        message=message,
                        channel=channel,
                        topic_id=topic_id,
                        image_file=image_file
                    )
                except Exception as e:
                    logger.error(f"Error processing image: {str(e)}")
                    return {"error": f"Error processing image: {str(e)}"}
            else:
                # 发送纯文本消息
                message_id = await self.core.send_message(
                    message=message,
                    channel=channel,
                    topic_id=topic_id
                )
            
            return {
                "status": "success",
                "message": "Message sent successfully",
                "message_id": message_id
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {"error": str(e)}

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