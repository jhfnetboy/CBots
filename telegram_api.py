import logging
import asyncio
from datetime import datetime
from telegram_core import TelegramCore
import base64
from io import BytesIO
import time
import aiohttp
import re
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class TelegramAPI:
    def __init__(self, core: TelegramCore = None):
        self.core = core or TelegramCore()
        self.is_running = False

    async def send_message(self, message: str, channel: str = None, topic_id: int = None, scheduled_time: str = None, image_data: str = None, image_url: str = None):
        """发送消息到 Telegram"""
        try:
            # 记录请求参数
            logger.info(f"TelegramAPI.send_message called with params: message={message}, channel={channel}, topic_id={topic_id}, scheduled_time={scheduled_time}, has_image={bool(image_data)}, has_image_url={bool(image_url)}")
            
            # 日志记录服务状态
            logger.info(f"Checking service status - core.is_running: {self.core.is_running if self.core else False}, client: {bool(self.core.client if self.core else False)}")
            
            # 检查客户端是否初始化
            if not self.core or not self.core.client:
                logger.error("Telegram client not initialized")
                return {'error': 'Telegram client not initialized'}
                
            # 记录定时发送的时间格式
            logger.info(f"scheduled_time type: {type(scheduled_time)}, value: {scheduled_time}")
            
            # 处理定时发送
            if scheduled_time:
                logger.info(f"Scheduling message for time: {scheduled_time}")
                try:
                    # 确保时间格式正确（去掉可能的Z后缀）
                    scheduled_time = scheduled_time.replace('Z', '')
                    scheduled_datetime = datetime.fromisoformat(scheduled_time)
                    now = datetime.now()
                    
                    if scheduled_datetime <= now:
                        logger.error("Scheduled time is in the past")
                        return {'error': 'Scheduled time must be in the future'}
                        
                    delay = (scheduled_datetime - now).total_seconds()
                    
                    # 将延迟时间转换为可读格式
                    days = int(delay // (24 * 3600))
                    hours = int((delay % (24 * 3600)) // 3600)
                    minutes = int((delay % 3600) // 60)
                    
                    logger.info(f"Message will be sent in {days} days, {hours} hours, {minutes} minutes")
                    
                    # 启动定时任务
                    asyncio.create_task(self._send_message_later(message, channel, topic_id, delay, image_data, image_url))
                    
                    # 返回定时发送的状态
                    return {
                        'status': 'scheduled',
                        'message': f"Message scheduled to be sent at {scheduled_datetime.isoformat()}",
                        'delay': {
                            'days': days,
                            'hours': hours,
                            'minutes': minutes,
                            'total_seconds': delay
                        }
                    }
                except ValueError as e:
                    logger.error(f"Invalid scheduled time format: {scheduled_time}")
                    return {'error': f'Invalid scheduled time format: {str(e)}'}
                    
            # 处理即时发送
            logger.info(f"Sending immediate message to channel: {channel}, topic_id: {topic_id}, has image: {bool(image_data)}, has image URL: {bool(image_url)}")
            
            # 处理图片
            image_file = None
            if image_data:
                try:
                    # 解码Base64图片数据
                    image_bytes = base64.b64decode(image_data.split(',')[1])
                    image_file = BytesIO(image_bytes)
                    image_file.name = 'image.jpg'  # 为文件对象添加名称属性
                except Exception as e:
                    logger.error(f"Error processing image data: {e}")
                    return {'error': f'Error processing image: {str(e)}'}
            elif image_url:
                try:
                    # 处理可能的Markdown格式
                    if image_url.startswith('!['):
                        # 从Markdown中提取URL，格式可能是 ![alt](url)
                        match = re.search(r'\!\[.*?\]\((.*?)\)', image_url)
                        if match:
                            image_url = match.group(1)
                        else:
                            return {'error': 'Invalid Markdown image format'}
                            
                    # 下载图片URL
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status != 200:
                                return {'error': f'Failed to download image from URL: {resp.status}'}
                            image_bytes = await resp.read()
                            image_file = BytesIO(image_bytes)
                            # 从URL中提取文件名
                            url_path = urlparse(image_url).path
                            file_name = os.path.basename(url_path) or 'image.jpg'
                            image_file.name = file_name
                except Exception as e:
                    logger.error(f"Error downloading image from URL: {e}")
                    return {'error': f'Error downloading image: {str(e)}'}
                    
            # 发送消息
            try:
                if self.core:
                    # 使用更新后的参数名调用core的send_message方法
                    result = await self.core.send_message(
                        message=message,
                        channel_name=channel, 
                        topic_id=topic_id, 
                        image_path=image_file
                    )
                    return result
                else:
                    logger.error("Telegram core not initialized")
                    return {'error': 'Telegram core not initialized'}
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                return {'error': str(e)}
                
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return {'error': str(e)}

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

    async def _send_message_later(self, message: str, channel: str, topic_id: int, delay: float, image_data: str = None, image_url: str = None):
        """在指定延迟后发送消息"""
        try:
            logger.info(f"Scheduled message task started with delay of {delay} seconds")
            
            # 等待指定的延迟时间
            await asyncio.sleep(delay)
            
            # 处理图片
            image_file = None
            if image_data:
                try:
                    # 解码Base64图片数据
                    image_bytes = base64.b64decode(image_data.split(',')[1])
                    image_file = BytesIO(image_bytes)
                    image_file.name = 'image.jpg'  # 为文件对象添加名称属性
                except Exception as e:
                    logger.error(f"Error processing scheduled image data: {e}")
                    return
            elif image_url:
                try:
                    # 处理可能的Markdown格式
                    if image_url.startswith('!['):
                        # 从Markdown中提取URL，格式可能是 ![alt](url)
                        match = re.search(r'\!\[.*?\]\((.*?)\)', image_url)
                        if match:
                            image_url = match.group(1)
                        else:
                            logger.error("Invalid Markdown image format")
                            return
                            
                    # 下载图片URL
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status != 200:
                                logger.error(f"Failed to download image from URL: {resp.status}")
                                return
                            image_bytes = await resp.read()
                            image_file = BytesIO(image_bytes)
                            # 从URL中提取文件名
                            url_path = urlparse(image_url).path
                            file_name = os.path.basename(url_path) or 'image.jpg'
                            image_file.name = file_name
                except Exception as e:
                    logger.error(f"Error downloading scheduled image from URL: {e}")
                    return
            
            logger.info(f"Sending scheduled message to channel: {channel}, topic_id: {topic_id}")
            
            # 发送消息
            if self.core:
                result = await self.core.send_message(
                    message=message,
                    channel_name=channel, 
                    topic_id=topic_id, 
                    image_path=image_file
                )
                if 'error' in result:
                    logger.error(f"Error sending scheduled message: {result['error']}")
                else:
                    logger.info(f"Scheduled message sent successfully!")
            else:
                logger.error("Telegram core not initialized for scheduled message")
                
        except Exception as e:
            logger.error(f"Error in _send_message_later: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}") 