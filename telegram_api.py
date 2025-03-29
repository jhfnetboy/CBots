import logging
import asyncio
from datetime import datetime
from telegram_core import TelegramCore

logger = logging.getLogger(__name__)

class TelegramAPI:
    def __init__(self):
        self.core = TelegramCore()
        self.is_running = False

    async def send_message(self, message: str, channel: str = None, topic_id: int = None, scheduled_time: str = None):
        """发送消息到 Telegram"""
        try:
            if not self.is_running:
                return {"error": "Telegram service is not running"}
            
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
            if not self.is_running:
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
            await self.core.start()
            self.is_running = True
            return {"status": "success", "message": "Telegram API service started"}
            
        except Exception as e:
            logger.error(f"Error starting Telegram API service: {str(e)}")
            return {"error": str(e)}

    async def stop(self):
        """停止 Telegram API 服务"""
        try:
            await self.core.stop()
            self.is_running = False
            return {"status": "success", "message": "Telegram API service stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping Telegram API service: {str(e)}")
            return {"error": str(e)} 