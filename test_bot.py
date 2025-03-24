from telethon import TelegramClient, events
from config import API_ID, API_HASH, BOT_TOKEN

async def main():
    print("Starting test bot...")
    client = TelegramClient('test_session', API_ID, API_HASH)
    
    @client.on(events.NewMessage)
    async def handler(event):
        print(f"Received message: {event.text}")
        await event.reply('Test bot received your message!')
    
    try:
        await client.start(bot_token=BOT_TOKEN)
        print("Bot started successfully!")
        print(f"Bot is running as: {await client.get_me()}")
        print("Waiting for messages...")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 