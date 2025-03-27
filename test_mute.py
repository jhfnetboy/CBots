import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import ChatBannedRights
from datetime import datetime, timedelta
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
TEST_GROUP_ID = os.getenv('TELEGRAM_DEFAULT_GROUP')  # 使用默认群组ID进行测试
TEST_USERNAME = "nicolasshuaishuai"  # 测试用户名

async def get_user_from_group(client, group_id, username):
    """从群组中获取用户信息"""
    try:
        logger.info(f"Attempting to get user {username} from group {group_id}")
        # 获取群组信息
        group = await client.get_entity(group_id)
        logger.info(f"Found group: {group.title}")
        
        # 获取群组成员
        async for member in client.iter_participants(group):
            if member.username and member.username.lower() == username.lower():
                logger.info(f"Found user: {member.first_name} (ID: {member.id}, Username: {member.username})")
                return member
                
        logger.error(f"User {username} not found in group {group_id}")
        return None
    except Exception as e:
        logger.error(f"Error getting user from group: {str(e)}")
        return None

async def test_mute_user(client, username):
    """测试禁言用户功能"""
    try:
        logger.info(f"Attempting to mute user {username} in group {TEST_GROUP_ID}")
        
        # 从群组中获取用户
        user = await get_user_from_group(client, TEST_GROUP_ID, username)
        if not user:
            logger.error("Could not find user in group")
            return False
            
        # 设置禁言时间为4小时
        until_date = datetime.now() + timedelta(hours=4)
        
        # 使用 edit_permissions 进行禁言
        await client.edit_permissions(
            TEST_GROUP_ID,
            user.id,
            until_date=until_date,
            send_messages=False,
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            use_inline_bots=False
        )
        
        logger.info(f"Successfully muted user {username}")
        return True
    except Exception as e:
        logger.error(f"Error muting user: {str(e)}")
        return False

async def test_unmute_user(client, username):
    """测试解除禁言功能"""
    try:
        logger.info(f"Attempting to unmute user {username} in group {TEST_GROUP_ID}")
        
        # 从群组中获取用户
        user = await get_user_from_group(client, TEST_GROUP_ID, username)
        if not user:
            logger.error("Could not find user in group")
            return False
            
        # 解除禁言
        await client.edit_permissions(
            TEST_GROUP_ID,
            user.id,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            use_inline_bots=True
        )
        
        logger.info(f"Successfully unmuted user {username}")
        return True
    except Exception as e:
        logger.error(f"Error unmuting user: {str(e)}")
        return False

async def main():
    """主函数"""
    # 创建客户端
    client = TelegramClient('test_session', API_ID, API_HASH)
    
    try:
        # 启动客户端
        await client.start(bot_token=BOT_TOKEN)
        logger.info("Client started successfully")
        
        # 测试禁言功能
        logger.info(f"Testing mute functionality for user: {TEST_USERNAME}")
        
        # 测试禁言
        mute_result = await test_mute_user(client, TEST_USERNAME)
        if mute_result:
            logger.info("Mute test passed")
        else:
            logger.error("Mute test failed")
            
        # 等待5秒
        await asyncio.sleep(5)
        
        # 测试解除禁言
        unmute_result = await test_unmute_user(client, TEST_USERNAME)
        if unmute_result:
            logger.info("Unmute test passed")
        else:
            logger.error("Unmute test failed")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        # 断开连接
        await client.disconnect()
        logger.info("Client disconnected")

if __name__ == '__main__':
    asyncio.run(main()) 