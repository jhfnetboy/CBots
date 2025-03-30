import logging
import asyncio
from datetime import datetime
from telegram_core import TelegramCore

logger = logging.getLogger(__name__)

class TelegramAPI:
    def __init__(self, core: TelegramCore = None):
        self.core = core or TelegramCore()
        self.is_running = False

    async def send_message(self, message: str, channel: str = None, topic_id: int = None, scheduled_time: str = None):
        """发送消息到 Telegram"""
        try:
            # 检查服务状态
            if not self.is_running:
                logger.error("Telegram API service is not running")
                return {"error": "Telegram service is not running"}
                
            if not self.core.is_running:
                logger.error("Telegram core service is not running")
                return {"error": "Telegram service is not running"}
            
            if not self.core.client:
                logger.error("Telegram client is not initialized")
                return {"error": "Telegram client not initialized"}
            
            if scheduled_time:
                # 解析计划时间
                scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                now = datetime.utcnow()
                
                if scheduled_datetime <= now:
                    return {"error": "Scheduled time must be in the future"}
                
                # 计算延迟时间
                delay = (scheduled_datetime - now).total_seconds()
                logger.info(f"Scheduling message for {scheduled_datetime} (delay: {delay}s)")
                await asyncio.sleep(delay)
            
            # 发送消息
            message_id = await self.core.send_message(message, channel, topic_id)
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