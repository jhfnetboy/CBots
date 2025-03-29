import logging
from web_service import WebService
from telegram_api import TelegramAPI
from twitter_api import TwitterAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """启动Web服务"""
    try:
        # 初始化API客户端
        telegram_api = TelegramAPI()
        twitter_api = TwitterAPI()
        
        # 初始化Web服务
        web_service = WebService(telegram_api, twitter_api)
        
        # 启动Web服务
        logger.info("Starting web service...")
        web_service.run_web_service(host='0.0.0.0', port=8872)
        
    except Exception as e:
        logger.error(f"Error in web service: {e}", exc_info=True)

if __name__ == "__main__":
    main() 