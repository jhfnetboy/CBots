"""
提供Telegram API服务，允许通过HTTP API访问Telegram功能
"""

import logging
import asyncio
from aiohttp import web
import json
from telegram_core import TelegramCore
import traceback
from datetime import datetime, timedelta
from image_sender import ImageSender
import re

logger = logging.getLogger(__name__)

class TelegramAPI:
    def __init__(self, core: TelegramCore = None):
        """初始化Telegram API服务"""
        self.core = core or TelegramCore()
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.is_running = False
        
        # 设置路由
        self.app.router.add_post('/send_message', self.handle_send_message)
        self.app.router.add_get('/status', self.handle_status)
        
        logger.info("TelegramAPI initialized")
        
    async def start(self):
        """启动 Telegram API 服务"""
        try:
            # 仅当core尚未启动时才启动它
            # 检查是否是从外部传入的core，如果不是，则需要启动它
            if not self.core.is_running:
                logger.info("核心服务尚未启动，尝试启动...")
                result = await self.core.start()
                if not result:
                    logger.error("Failed to start Telegram core service")
                    return False
                logger.info("核心服务启动成功")
            else:
                logger.info("使用已经启动的核心服务")
             
            # 启动API服务
            self.is_running = True
            logger.info("Telegram API service started successfully")
            return True
             
        except Exception as e:
            logger.error(f"Error starting Telegram API service: {str(e)}")
            logger.error(traceback.format_exc())
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
            
    async def handle_send_message(self, request):
        """处理发送消息请求"""
        try:
            if not self.core or not self.core.is_running:
                return web.json_response({"success": False, "error": "Telegram core service is not running"}, status=503)
                
            data = await request.json()
            
            # 检查必要参数
            if 'message' not in data:
                return web.json_response({"success": False, "error": "Missing 'message' parameter"}, status=400)
                
            message = data.get('message')
            channel = data.get('channel')
            topic_id = data.get('topic_id')
            image_data = data.get('image_data')
            
            # 发送消息
            success = await self.core.send_message(
                message=message,
                channel=channel,
                topic_id=topic_id,
                image_data=image_data
            )
            
            if success:
                return web.json_response({"success": True})
            else:
                return web.json_response({"success": False, "error": "Failed to send message"}, status=500)
                
        except Exception as e:
            logger.error(f"Error handling send_message request: {e}")
            logger.error(traceback.format_exc())
            return web.json_response({"success": False, "error": str(e)}, status=500)
            
    async def handle_status(self, request):
        """处理状态请求"""
        try:
            status = {
                "api_running": self.is_running,
                "core_running": self.core.is_running if self.core else False,
                "version": "0.8.4"
            }
            
            return web.json_response(status)
            
        except Exception as e:
            logger.error(f"Error handling status request: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def send_message(self, message, channel=None, topic_id=None, scheduled_time=None, image_data=None, image_url=None, group_name=None, image=None, reply_to=None):
        """发送消息到指定频道或群组"""
        try:
            if not self.core.is_running:
                return {"error": "Telegram core service is not running"}

            # 发送消息
            result = await self.core.send_message(
                message=message,
                channel=channel,
                topic_id=topic_id,
                image_data=image_data,
                image_url=image_url,
                group_name=group_name,
                image=image,
                reply_to=reply_to
            )
            
            if isinstance(result, dict) and "error" in result:
                return result
            
            return {"message_id": str(result)}
            
        except Exception as e:
            logger.error(f"Error sending message via API: {e}")
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

    async def connect(self):
        """连接到Telegram服务，适用于PythonAnywhere环境"""
        try:
            # 直接使用已存在的core对象
            if not self.core.client or not self.core.client.is_connected():
                await self.core.client.connect()
                
            self.is_running = True
            return {"status": "success", "message": "Connected to Telegram"}
            
        except Exception as e:
            logger.error(f"Error connecting to Telegram: {e}")
            return {"error": str(e)}
    
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

    def extract_topic_id(self, channel_input):
        """从 'Channel_Name/12345' 格式提取话题ID"""
        if not channel_input or '/' not in channel_input:
            return None, channel_input
            
        parts = channel_input.split('/')
        if len(parts) != 2:
            return None, channel_input
            
        channel_name = parts[0].strip()
        try:
            topic_id = int(parts[1].strip())
            return topic_id, channel_name
        except ValueError:
            return None, channel_input 