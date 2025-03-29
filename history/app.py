import os
import json
import logging
import asyncio
from datetime import datetime
from flask import Flask
from telethon import TelegramClient, events
from command_manager import CommandManager
from bot_handlers import BotHandlers
from dotenv import load_dotenv
from web_routes import init_web_routes, set_main_loop, VERSION
from twitter_routes import init_twitter_routes, set_main_loop as set_twitter_main_loop

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize managers
command_manager = CommandManager()
bot_handlers = BotHandlers()

# Initialize Flask app
app = Flask(__name__)

# Configuration
PORT = int(os.getenv('PORT', 8872))

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def create_client():
    """Create and return a new TelegramClient instance"""
    return TelegramClient('bot_session', API_ID, API_HASH)

async def init_client(client):
    """Initialize the client with bot token"""
    await client.start(bot_token=BOT_TOKEN)
    return client

async def schedule_tasks(client):
    """Schedule daily tasks"""
    while True:
        now = datetime.now()
        if now.hour == 9:  # 9:00 AM
            await bot_handlers.send_daily_password(client)
        
        # Check for users to unmute
        await bot_handlers.check_unmute_users(client)
        await asyncio.sleep(60)  # Check every minute

def setup_handlers(client):
    """Set up event handlers for the client"""
    
    @client.on(events.NewMessage)
    async def handle_message(event):
        # Log all incoming messages
        logger.info(f"Received message: {event.message.text} from {event.sender_id} in chat {event.chat_id}")
        await bot_handlers.handle_message(event, command_manager)

    @client.on(events.ChatAction)
    async def handle_new_member(event):
        # Log chat actions
        if event.user_joined:
            logger.info(f"New member joined: {event.user_id} in chat {event.chat_id}")
            await bot_handlers.handle_new_member(event, client)

    @client.on(events.NewMessage(func=lambda e: e.is_private))
    async def handle_private_message(event):
        # Log private messages
        logger.info(f"Private message: {event.message.text} from {event.sender_id}")
        await bot_handlers.handle_private_message(event, client)

def run_flask(client):
    """Run Flask in a separate thread"""
    # Initialize web routes
    init_web_routes(app, client)
    init_twitter_routes(app)
    
    # Create and set event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Set the main event loop for both web and twitter routes
    set_main_loop(loop)
    set_twitter_main_loop(loop)
    
    app.run(host='0.0.0.0', port=PORT)

async def main():
    """Main function to run the bot"""
    # Create and initialize client
    client = create_client()
    await init_client(client)
    
    # Set up event handlers
    setup_handlers(client)
    
    # Send online message
    await bot_handlers.send_online_message(client)
    
    # Start the scheduler
    scheduler_task = asyncio.create_task(schedule_tasks(client))
    
    # Run Flask in a separate thread
    import threading
    flask_thread = threading.Thread(target=run_flask, args=(client,))
    flask_thread.daemon = True
    flask_thread.start()
    
    try:
        # Keep the bot running
        await client.run_until_disconnected()
    finally:
        # Clean up
        await client.disconnect()
        scheduler_task.cancel()

if __name__ == '__main__':
    # Print version at startup
    print(f"\n=== Telegram Bot v{VERSION} ===\n")
    
    # Run the main function
    asyncio.run(main()) 