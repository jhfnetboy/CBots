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
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.client = None
        self.is_running = False
        logger.info("TwitterCore initialized")

    async def start(self):
        """Start the Twitter core service"""
        try:
            logger.info("Starting Twitter core service...")
            if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret, self.bearer_token]):
                missing = []
                if not self.api_key: missing.append('TWITTER_API_KEY')
                if not self.api_secret: missing.append('TWITTER_API_SECRET')
                if not self.access_token: missing.append('TWITTER_ACCESS_TOKEN')
                if not self.access_token_secret: missing.append('TWITTER_ACCESS_TOKEN_SECRET')
                if not self.bearer_token: missing.append('TWITTER_BEARER_TOKEN')
                raise ValueError(f"Missing required Twitter API credentials: {', '.join(missing)}")
            
            # 初始化Twitter客户端 (v2)
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            
            # 测试API连接
            me = self.client.get_me()
            logger.info(f"Twitter API credentials verified successfully. Connected as: {me.data.username}")
            
            # 设置服务状态为运行中
            self.is_running = True
            logger.info("Twitter core service started successfully - is_running: True")
            return True
            
        except Exception as e:
            self.is_running = False
            logger.error(f"Error starting Twitter core service: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop the Twitter core service"""
        try:
            logger.info("Stopping Twitter core service...")
            self.is_running = False
            logger.info("Twitter core service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Twitter core service: {e}", exc_info=True)
            raise

    async def send_tweet(self, message: str, scheduled_time: str = None) -> str:
        """发送推文"""
        try:
            if not self.client:
                logger.error("Twitter client not initialized")
                raise Exception("Twitter client not initialized")
                
            logger.info(f"Attempting to send tweet: {message}")
            
            if scheduled_time:
                # 解析计划时间
                scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                now = datetime.utcnow()
                
                if scheduled_datetime <= now:
                    return {"error": "Scheduled time must be in the future"}
                
                # 计算延迟时间
                delay = (scheduled_datetime - now).total_seconds()
                logger.info(f"Scheduling tweet for {scheduled_datetime} (delay: {delay}s)")
                await asyncio.sleep(delay)
            
            # 使用 v2 API 发送推文
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
            raise

    async def get_status(self):
        """获取 Twitter 服务状态"""
        try:
            if not self.client:
                return {"status": "stopped"}
            
            if not self.is_running:
                return {"status": "stopped"}
                
            me = self.client.get_me()
            return {
                "status": "running",
                "username": me.data.username,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {"error": str(e)} 