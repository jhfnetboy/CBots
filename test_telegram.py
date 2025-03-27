import asyncio
import os
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, PeerChannel, InputChannel
from telethon.utils import get_peer_id, resolve_id
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.channels import GetForumTopicsRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def test_channel_entity():
    """Test different methods to get channel entity"""
    client = TelegramClient('test_session', API_ID, API_HASH)
    
    try:
        # Start the client
        await client.start(bot_token=BOT_TOKEN)
        print("Client started successfully")
        
        # Test channel input
        community = "Account_Abstraction_Community"
        topic_id = 2817
        
        # 方法1: 使用社区名称获取社区实体并发送消息到话题
        print("\nMethod 1: Send message to topic")
        try:
            # 获取社区实体
            community_entity = await client.get_entity(community)
            print(f"Got community entity: {community_entity.id}")
            
            # 直接发送消息到话题
            print(f"\nTrying to send message to topic {topic_id}")
            message = await client.send_message(
                entity=community_entity,
                message="Test message to topic",
                reply_to=topic_id
            )
            print(f"Message sent successfully: {message}")
            
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(test_channel_entity()) 