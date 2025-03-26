import os
import requests
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_webhook():
    """设置 Telegram webhook"""
    try:
        # 从环境变量获取配置
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        netlify_url = os.getenv('NETLIFY_URL')  # 例如：https://your-app-name.netlify.app
        
        if not bot_token or not netlify_url:
            logger.error("Missing required environment variables")
            return
            
        # 构建 webhook URL
        webhook_url = f"{netlify_url}/.netlify/functions/app/webhook"
        
        # 设置 webhook
        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        data = {
            "url": webhook_url,
            "allowed_updates": ["message", "edited_message", "callback_query"]
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info(f"Webhook set successfully to: {webhook_url}")
                logger.info(f"Webhook info: {result.get('result')}")
            else:
                logger.error(f"Failed to set webhook: {result.get('description')}")
        else:
            logger.error(f"Failed to set webhook. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")

if __name__ == "__main__":
    set_webhook() 