import logging
import asyncio
from datetime import datetime
from twitter_core import TwitterCore

logger = logging.getLogger(__name__)

class TwitterAPI:
    def __init__(self):
        self.core = TwitterCore()
        self.is_running = False

    async def send_tweet(self, message: str, scheduled_time: str = None):
        """发送推文"""
        try:
            if not self.is_running:
                return {"error": "Twitter service is not running"}
            
            tweet_url = await self.core.send_tweet(message, scheduled_time)
            return {
                "status": "success",
                "message": "Tweet sent successfully",
                "tweet_url": tweet_url
            }
            
        except Exception as e:
            logger.error(f"Error sending tweet: {str(e)}")
            return {"error": str(e)}

    async def get_status(self):
        """获取 Twitter 服务状态"""
        try:
            if not self.is_running:
                return {"status": "stopped"}
            
            return await self.core.get_status()
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {"error": str(e)}

    async def start(self):
        """启动 Twitter API 服务"""
        try:
            await self.core.start()
            self.is_running = True
            return {"status": "success", "message": "Twitter API service started"}
            
        except Exception as e:
            logger.error(f"Error starting Twitter API service: {str(e)}")
            return {"error": str(e)}

    async def stop(self):
        """停止 Twitter API 服务"""
        try:
            await self.core.stop()
            self.is_running = False
            return {"status": "success", "message": "Twitter API service stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping Twitter API service: {str(e)}")
            return {"error": str(e)} 