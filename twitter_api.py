import logging
import os
import asyncio
import tweepy
from datetime import datetime
import base64
import io
from twitter_core import TwitterCore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TwitterAPI:
    def __init__(self, core: TwitterCore = None):
        self.core = core or TwitterCore()
        self.is_running = False
        logger.info("TwitterAPI initialized")

    async def send_tweet(self, message: str, scheduled_time: str = None, image_data: str = None, image_url: str = None):
        """Send a tweet with optional image"""
        try:
            logger.info(f"Sending tweet: {message}")
            
            # 检查服务状态
            status_info = await self.get_status()
            if status_info["status"] != "running":
                logger.error(f"Twitter service status: {status_info}")
                return {"error": status_info["message"]}
            
            # 检查参数
            if not message and not image_data and not image_url:
                return {"error": "Message or image is required"}
                
            # 处理定时发送
            if scheduled_time:
                try:
                    # 格式化时间去掉Z后缀
                    scheduled_time = scheduled_time.replace('Z', '')
                    scheduled_datetime = datetime.fromisoformat(scheduled_time)
                    now = datetime.now()
                    
                    # 验证时间是否在未来
                    if scheduled_datetime <= now:
                        return {"error": "Scheduled time must be in the future"}
                        
                    delay = (scheduled_datetime - now).total_seconds()
                    logger.info(f"Tweet scheduled to be sent after {delay} seconds")
                    
                    # 设置延迟任务
                    await asyncio.sleep(delay)
                    logger.info(f"Executing scheduled tweet after delay")
                    
                except ValueError as e:
                    logger.error(f"Invalid scheduled time format: {scheduled_time}")
                    return {"error": f"Invalid scheduled time format: {str(e)}"}
            
            media_id = None
            
            # 处理图片
            if image_data:
                try:
                    logger.info("Processing image data...")
                    # 解码Base64图片数据
                    if image_data.startswith('data:image'):
                        # 移除data URI前缀
                        image_data = image_data.split(',')[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    image_io = io.BytesIO(image_bytes)
                    
                    # 上传图片到Twitter
                    media = self.core.client.media_upload(file=image_io)
                    media_id = media.media_id
                    logger.info(f"Image uploaded to Twitter with media ID: {media_id}")
                except Exception as e:
                    logger.error(f"Error processing image: {e}")
                    return {"error": f"Error processing image: {str(e)}"}
            
            # 处理图片URL
            elif image_url:
                try:
                    logger.info(f"Processing image URL: {image_url}")
                    # 如果是Markdown格式，提取URL
                    if image_url.startswith('!['):
                        import re
                        match = re.search(r'\]\((.*?)\)', image_url)
                        if match:
                            image_url = match.group(1)
                    
                    # 上传图片到Twitter
                    media = self.core.client.media_upload(image_url)
                    media_id = media.media_id
                    logger.info(f"Image from URL uploaded to Twitter with media ID: {media_id}")
                except Exception as e:
                    logger.error(f"Error processing image URL: {e}")
                    return {"error": f"Error processing image URL: {str(e)}"}
            
            # 发送推文
            if media_id:
                # 发送带图片的推文
                tweet = self.core.client.create_tweet(text=message, media_ids=[media_id])
            else:
                # 发送纯文本推文
                tweet = self.core.client.create_tweet(text=message)
            
            logger.info(f"Tweet sent successfully! Tweet ID: {tweet.data['id']}")
            result = {
                "status": "scheduled" if scheduled_time else "success",
                "message": "Tweet scheduled for sending" if scheduled_time else "Tweet sent successfully",
                "tweet_id": tweet.data['id']
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending tweet: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return {"error": str(e)}

    async def get_status(self):
        """Get Twitter API service status"""
        if not self.core:
            return {"status": "error", "message": "Twitter core not initialized"}
        
        if not self.core.is_running:
            return {"status": "stopped", "message": "Twitter service is not running"}
            
        if not self.core.client:
            return {"status": "error", "message": "Twitter client not initialized"}
            
        return {"status": "running", "message": "Twitter service is running"}

    async def start(self):
        """Start the Twitter API service"""
        try:
            if not self.core:
                return False
            
            if not self.core.is_running:
                await self.core.start()
                
            if not self.core.is_running:
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error starting Twitter API service: {e}")
            return False
            
    async def stop(self):
        """Stop the Twitter API service"""
        try:
            if self.core:
                await self.core.stop()
            return True
        except Exception as e:
            logger.error(f"Error stopping Twitter API service: {e}")
            return False 