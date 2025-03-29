import logging
import os
import tweepy
from datetime import datetime
import asyncio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TwitterCore:
    def __init__(self):
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.client = None
        self.is_running = False
        self._loop = None
        self._scheduled_tasks = set()
        logger.info("TwitterCore initialized")

    async def start(self):
        """启动Twitter客户端"""
        try:
            if not self._loop:
                self._loop = asyncio.get_event_loop()
                
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            
            self.is_running = True
            logger.info("Twitter service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting Twitter service: {e}")
            return False
            
    async def stop(self):
        """停止Twitter客户端"""
        try:
            # 取消所有定时任务
            for task in self._scheduled_tasks:
                task.cancel()
            self._scheduled_tasks.clear()
            
            self.is_running = False
            logger.info("Twitter service stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping Twitter service: {e}")
            return False
            
    async def send_tweet(self, message: str, scheduled_time: str = None) -> dict:
        """发送推文"""
        try:
            if not self.client or not self.is_running:
                return {"error": "Twitter service is not running"}
                
            logger.info(f"Attempting to send tweet: {message}")
            
            if scheduled_time:
                # 解析计划时间
                scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                now = datetime.utcnow()
                
                if scheduled_datetime <= now:
                    return {"error": "Scheduled time must be in the future"}
                    
                # 计算延迟时间
                delay = (scheduled_datetime - now).total_seconds()
                
                # 创建定时任务
                task = asyncio.create_task(self._send_scheduled_tweet(message, delay))
                self._scheduled_tasks.add(task)
                task.add_done_callback(self._scheduled_tasks.discard)
                
                # 计算天、小时、分钟
                days = int(delay // (24 * 3600))
                hours = int((delay % (24 * 3600)) // 3600)
                minutes = int((delay % 3600) // 60)
                
                # 构建提示信息
                timing_info = []
                if days > 0:
                    timing_info.append(f"{days} days ")
                if hours > 0:
                    timing_info.append(f"{hours} hours ")
                if minutes > 0:
                    timing_info.append(f"{minutes} minutes")
                    
                timing_str = "".join(timing_info).strip()
                logger.info(f"Scheduling tweet for {scheduled_datetime} (delay: {delay}s)")
                
                return {
                    "status": "scheduled",
                    "message": f"Tweet scheduled successfully. Will be sent in {timing_str}",
                    "scheduled_time": scheduled_datetime.isoformat()
                }
            
            # 立即发送推文
            response = self.client.create_tweet(text=message)
            tweet_id = response.data['id']
            
            # 获取用户信息以构建推文URL
            me = self.client.get_me()
            username = me.data.username
            
            # 构建推文URL
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
            logger.info(f"Tweet sent successfully. URL: {tweet_url}")
            return tweet_url
            
        except Exception as e:
            logger.error(f"Error sending tweet: {e}", exc_info=True)
            return {"error": str(e)}
            
    async def _send_scheduled_tweet(self, message: str, delay: float):
        """后台任务：发送定时推文"""
        try:
            await asyncio.sleep(delay)
            
            # 发送推文
            response = self.client.create_tweet(text=message)
            tweet_id = response.data['id']
            
            # 获取用户信息以构建推文URL
            me = self.client.get_me()
            username = me.data.username
            
            # 构建推文URL
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
            logger.info(f"Scheduled tweet sent successfully. URL: {tweet_url}")
            
        except Exception as e:
            logger.error(f"Error sending scheduled tweet: {e}", exc_info=True)
            
    async def get_status(self) -> dict:
        """获取服务状态"""
        try:
            if not self.client or not self.is_running:
                return {
                    "status": "stopped",
                    "message": "Twitter service is not running"
                }
                
            # 获取用户信息
            me = self.client.get_me()
            
            return {
                "status": "running",
                "message": "Twitter service is running",
                "username": me.data.username,
                "name": me.data.name,
                "followers_count": me.data.public_metrics.get('followers_count', 0),
                "following_count": me.data.public_metrics.get('following_count', 0),
                "tweet_count": me.data.public_metrics.get('tweet_count', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting Twitter status: {e}")
            return {
                "status": "error",
                "message": str(e)
            } 