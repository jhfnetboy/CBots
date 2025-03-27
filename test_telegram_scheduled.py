import os
import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_scheduled_message():
    """Test sending a scheduled message to a Telegram topic"""
    try:
        # Get Telegram credentials
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not all([api_id, api_hash, bot_token]):
            print("Error: Missing Telegram credentials in .env file")
            return
            
        # Initialize client
        client = TelegramClient('bot_session', api_id, api_hash)
        await client.start(bot_token=bot_token)
        print("Client started successfully")
        
        # Test parameters
        community_name = "Account_Abstraction_Community"
        topic_id = 2817
        message = "This is a test scheduled message to topic"
        scheduled_time = datetime.utcnow() + timedelta(minutes=1)  # Schedule 1 minute from now
        
        # Get community entity
        community = await client.get_entity(community_name)
        print(f"Got community: {community.title} (ID: {community.id})")
        
        # Calculate delay
        delay = (scheduled_time - datetime.utcnow()).total_seconds()
        print(f"Scheduling message for {scheduled_time} (delay: {delay}s)")
        
        # Wait until scheduled time
        await asyncio.sleep(delay)
        
        # Send message
        response = await client.send_message(
            community,
            message,
            reply_to=topic_id
        )
        print(f"Message sent successfully! Message ID: {response.id}")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"Error testing scheduled message: {str(e)}")

if __name__ == '__main__':
    asyncio.run(test_scheduled_message()) 