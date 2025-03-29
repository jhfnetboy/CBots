import logging
import os
import tweepy
from command_manager import command_manager, BotType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TwitterBot:
    def __init__(self):
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.client = None
        logger.info("TwitterBot initialized")

    async def start(self):
        """Start the Twitter bot"""
        try:
            logger.info("=== Starting Twitter Bot Initialization ===")
            # 验证API凭证
            if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
                missing = []
                if not self.api_key: missing.append('TWITTER_API_KEY')
                if not self.api_secret: missing.append('TWITTER_API_SECRET')
                if not self.access_token: missing.append('TWITTER_ACCESS_TOKEN')
                if not self.access_token_secret: missing.append('TWITTER_ACCESS_TOKEN_SECRET')
                raise ValueError(f"Missing required Twitter API credentials: {', '.join(missing)}")
            
            # 初始化Twitter客户端 (v2)
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            
            # 测试API连接
            me = self.client.get_me()
            logger.info(f"Twitter API credentials verified successfully. Connected as: {me.data.username}")
            
            # 注册命令处理器
            command_manager.register_command('start', self.handle_start, BotType.TWITTER)
            command_manager.register_command('help', self.handle_help, BotType.TWITTER)
            command_manager.register_command('hi', self.handle_hi, BotType.TWITTER)
            command_manager.register_message_handler(self.handle_message, BotType.TWITTER)
            
            logger.info("=== Twitter Bot Initialization Complete ===")
            return True
        except Exception as e:
            logger.error(f"Error initializing Twitter bot: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop the Twitter bot"""
        try:
            if self.client:
                logger.info("Stopping Twitter bot...")
                logger.info("Twitter bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Twitter bot: {e}", exc_info=True)
            raise

    async def handle_start(self, event):
        """Handle /start command"""
        try:
            await event.reply("Hello! I'm your Twitter bot. Use /help to see available commands.")
        except Exception as e:
            logger.error(f"Error handling start command: {e}", exc_info=True)

    async def handle_help(self, event):
        """Handle /help command"""
        try:
            help_text = "Available commands:\n/start - Start the bot\n/help - Show this help message\n/hi - Say hello"
            await event.reply(help_text)
        except Exception as e:
            logger.error(f"Error handling help command: {e}", exc_info=True)

    async def handle_hi(self, event):
        """Handle /hi command"""
        try:
            await event.reply("Hi there! 👋")
        except Exception as e:
            logger.error(f"Error handling hi command: {e}", exc_info=True)

    async def handle_message(self, message: str, event):
        """Handle non-command messages"""
        try:
            await event.reply(f"Received: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    async def send_tweet(self, message: str) -> str:
        """Send a tweet and return the tweet URL"""
        try:
            if not self.client:
                logger.error("Twitter client not initialized")
                raise Exception("Twitter client not initialized")
                
            logger.info(f"Attempting to send tweet: {message}")
            
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