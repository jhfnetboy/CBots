import asyncio
import os
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, PeerChannel
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
        
        # Test channel ID
        channel_id = 2817  # 从 Account_Abstraction_Community/2817 提取的数字
        
        # 方法1: 使用 InputPeerChannel
        print("\nMethod 1: Using InputPeerChannel")
        try:
            entity = await client.get_entity(InputPeerChannel(channel_id, 0))
            print(f"Success with InputPeerChannel: {entity}")
        except Exception as e:
            print(f"Failed with InputPeerChannel: {str(e)}")
            
        # 方法2: 使用 PeerChannel
        print("\nMethod 2: Using PeerChannel")
        try:
            entity = await client.get_entity(PeerChannel(channel_id))
            print(f"Success with PeerChannel: {entity}")
        except Exception as e:
            print(f"Failed with PeerChannel: {str(e)}")
            
        # 方法3: 使用 -100 前缀
        print("\nMethod 3: Using -100 prefix")
        try:
            entity = await client.get_entity(-1002817)
            print(f"Success with -100 prefix: {entity}")
        except Exception as e:
            print(f"Failed with -100 prefix: {str(e)}")
            
        # 方法4: 使用 get_peer_id
        print("\nMethod 4: Using get_peer_id")
        try:
            from telethon.utils import get_peer_id
            peer_id = get_peer_id(PeerChannel(channel_id))
            print(f"Peer ID: {peer_id}")
            entity = await client.get_entity(peer_id)
            print(f"Success with get_peer_id: {entity}")
        except Exception as e:
            print(f"Failed with get_peer_id: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(test_channel_entity()) 