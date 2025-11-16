import os
import asyncio
from telethon import TelegramClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Test parameters
TEST_GROUP = "Account_Abstraction_Community"
TEST_TOPIC_ID = 18472
TEST_MESSAGE = "这是一条测试消息"

async def send_message_to_topic():
    """发送消息到指定主题"""
    # 创建客户端
    client = TelegramClient('test_session', API_ID, API_HASH)
    
    try:
        # 启动客户端
        await client.start(bot_token=BOT_TOKEN)
        logger.info("Client started successfully")
        
        # 获取群组实体
        logger.info(f"Attempting to get entity for group: {TEST_GROUP}")
        group = await client.get_entity(TEST_GROUP)
        logger.info(f"Found group: {group.title} (ID: {group.id})")
        
        # 发送消息
        logger.info(f"Attempting to send message to topic {TEST_TOPIC_ID}")
        logger.info(f"Message content: {TEST_MESSAGE}")
        
        try:
            # 尝试发送消息
            response = await client.send_message(
                group,
                TEST_MESSAGE,
                reply_to=TEST_TOPIC_ID
            )
            logger.info(f"Message sent successfully! Message ID: {response.id}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        return False
    finally:
        # 断开连接
        await client.disconnect()
        logger.info("Client disconnected")

if __name__ == '__main__':
    asyncio.run(send_message_to_topic()) 