"""
PythonAnywhere兼容的Telegram API实现
简化版，避免长连接和复杂初始化
"""
import os
import json
import time
import logging
import traceback
import base64
import re
import requests
from io import BytesIO
from datetime import datetime
import asyncio

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramAPI:
    """
    Telegram API的PythonAnywhere兼容实现
    提供在PythonAnywhere环境中发送Telegram消息的功能
    """
    
    def __init__(self):
        """初始化API"""
        self.api_id = os.environ.get('TELEGRAM_API_ID')
        self.api_hash = os.environ.get('TELEGRAM_API_HASH')
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.phone = os.environ.get('TELEGRAM_PHONE')
        
        self.connected = False
        # 引入ImageSender处理图片
        from image_sender import ImageSender
        self.image_sender = ImageSender
        logger.info("TelegramAPI (PythonAnywhere) 初始化完成")
    
    async def connect(self):
        """连接到Telegram"""
        try:
            # 在PythonAnywhere环境中，我们不保持长连接
            # 每次请求时重新连接
            logger.info("Telegram API准备连接")
            
            # 导入telethon及核心组件
            from telethon import TelegramClient, functions, types
            
            # 创建session文件路径
            session_path = "telegram_session_pa"
            
            # 创建客户端
            self.client = TelegramClient(
                session_path,
                api_id=int(self.api_id),
                api_hash=self.api_hash
            )
            
            # 连接并登录
            await self.client.start(bot_token=self.bot_token)
            
            # 检查连接状态
            self.connected = self.client.is_connected()
            logger.info(f"Telegram API连接状态: {self.connected}")
            
            return self.connected
            
        except Exception as e:
            logger.error(f"连接到Telegram失败: {e}")
            logger.error(traceback.format_exc())
            self.connected = False
            return False
    
    async def disconnect(self):
        """断开连接"""
        try:
            if hasattr(self, 'client') and self.client:
                await self.client.disconnect()
                logger.info("Telegram API已断开连接")
            self.connected = False
            return True
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")
            return False

    async def get_status(self):
        """获取连接状态"""
        return {
            "connected": self.connected,
            "api_id": bool(self.api_id),
            "api_hash": bool(self.api_hash),
            "bot_token": bool(self.bot_token)
        }
    
    async def send_message(self, message, channel=None, image_data=None, scheduled_time=None):
        """
        发送消息到Telegram组/频道
        
        Args:
            message (str): 要发送的消息文本
            channel (str): 频道/组名称
            image_data (str): 图片数据 (Base64/URL/文件路径)
            scheduled_time (str): 定时发送的时间(ISO格式)
            
        Returns:
            dict: 结果信息
        """
        try:
            # 记录请求参数
            logger.info(f"准备发送消息到: {channel}")
            logger.info(f"消息长度: {len(message) if message else 0}")
            logger.info(f"包含图片: {bool(image_data)}, 定时发送: {bool(scheduled_time)}")
            
            # 确保连接
            if not self.connected:
                logger.warning("Telegram客户端未连接，尝试连接")
                await self.connect()
                if not self.connected:
                    return {"success": False, "error": "无法连接到Telegram API"}
            
            # 处理定时发送
            schedule_time = None
            if scheduled_time:
                try:
                    schedule_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                    # 检查时间是否在未来
                    if schedule_time <= datetime.now():
                        logger.warning(f"定时时间已过期: {schedule_time}")
                        return {"success": False, "error": "定时发送时间必须在未来"}
                    logger.info(f"消息将在 {schedule_time} 发送")
                except ValueError as e:
                    logger.error(f"无效的定时格式: {e}")
                    return {"success": False, "error": f"无效的定时格式: {e}"}
            
            # 获取目标实体
            try:
                entity = await self.client.get_entity(channel)
                logger.info(f"找到实体: {getattr(entity, 'title', channel)} (ID: {entity.id})")
            except Exception as e:
                logger.error(f"找不到实体 '{channel}': {e}")
                return {"success": False, "error": f"找不到频道/组: {channel}"}
            
            # 处理图片
            if image_data:
                try:
                    # 使用 ImageSender 处理图片
                    image_file = None
                    
                    # 处理Base64图片数据
                    if isinstance(image_data, str) and image_data.startswith('data:image/'):
                        logger.info("处理Base64图片数据")
                        image_file = await self.image_sender.prepare_image_from_base64(image_data)
                    
                    # 处理Markdown图片引用
                    elif isinstance(image_data, str) and re.match(r'!\[.*?\]\((.*?)\)', image_data):
                        url_match = re.match(r'!\[.*?\]\((.*?)\)', image_data)
                        if url_match:
                            image_url = url_match.group(1)
                            logger.info(f"从Markdown提取图片URL: {image_url}")
                            image_file = await self.image_sender.prepare_image_from_url(image_url)
                    
                    # 处理图片URL
                    elif isinstance(image_data, str) and image_data.startswith(('http://', 'https://')):
                        logger.info(f"从URL处理图片: {image_data}")
                        image_file = await self.image_sender.prepare_image_from_url(image_data)
                    
                    # 处理文件路径
                    elif isinstance(image_data, str) and os.path.exists(image_data):
                        logger.info(f"从文件路径处理图片: {image_data}")
                        with open(image_data, 'rb') as f:
                            file_content = f.read()
                            image_file = BytesIO(file_content)
                            image_file.name = os.path.basename(image_data)
                    
                    if not image_file:
                        return {"success": False, "error": "处理图片失败"}
                        
                    # 发送带图片的消息
                    result_id = await self.image_sender.send_image_message(
                        client=self.client,
                        entity=entity,
                        message=message,
                        image_file=image_file
                    )
                    
                    logger.info(f"带图片的消息发送成功，ID: {result_id}")
                    return {
                        "success": True,
                        "message_id": result_id,
                        "group": channel,
                        "scheduled": bool(scheduled_time)
                    }
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"发送带图片的消息失败: {error_msg}")
                    logger.error(traceback.format_exc())
                    return {"success": False, "error": f"发送失败: {error_msg}"}
            else:
                # 发送纯文本消息
                try:
                    sent_message = await self.client.send_message(
                        entity=entity,
                        message=message,
                        schedule=schedule_time
                    )
                    
                    logger.info(f"纯文本消息发送成功，ID: {sent_message.id}")
                    return {
                        "success": True,
                        "message_id": sent_message.id,
                        "group": channel,
                        "scheduled": bool(scheduled_time)
                    }
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"发送纯文本消息失败: {error_msg}")
                    logger.error(traceback.format_exc())
                    return {"success": False, "error": f"发送失败: {error_msg}"}
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"发送消息时出错: {error_msg}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": error_msg}

# 测试代码
if __name__ == "__main__":
    async def test():
        api = TelegramAPI()
        await api.connect()
        result = await api.send_message("测试消息", "your_channel")
        print(result)
        await api.disconnect()
    
    asyncio.run(test()) 