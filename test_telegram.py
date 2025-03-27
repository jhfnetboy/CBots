import asyncio
import os
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, PeerChannel, InputChannel
from telethon.utils import get_peer_id, resolve_id
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
        channel_id = 2817
        
        # 方法1: 使用社区名称获取社区实体
        print("\nMethod 1: Get community entity")
        try:
            community_entity = await client.get_entity(community)
            print(f"Community entity: {community_entity}")
            print(f"Community ID: {community_entity.id}")
            print(f"Community Access Hash: {community_entity.access_hash}")
            
            # 尝试不同的频道 ID 组合
            combinations = [
                (f"{community_entity.id}/{channel_id}", "Community ID/Channel ID"),
                (f"-100{channel_id}", "-100 + Channel ID"),
                (f"{community_entity.id}_{channel_id}", "Community ID_Channel ID"),
                (channel_id, "Raw Channel ID"),
                (f"{community}/{channel_id}", "Community Name/Channel ID")
            ]
            
            for channel_input, desc in combinations:
                print(f"\nTrying {desc}: {channel_input}")
                try:
                    entity = await client.get_entity(channel_input)
                    print(f"Success! Entity: {entity}")
                    
                    # 尝试发送测试消息
                    message = await client.send_message(entity, f"Test message to {desc}")
                    print(f"Message sent successfully: {message}")
                    break
                except Exception as e:
                    print(f"Failed: {str(e)}")
            
        except Exception as e:
            print(f"Failed with community: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(test_channel_entity()) 