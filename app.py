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
from web_routes import init_web_routes

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

def create_client():
    """Create and return a new TelegramClient instance"""
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    return TelegramClient('bot', api_id, api_hash)

async def init_client(client):
    """Initialize the client with bot token"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    await client.start(bot_token=bot_token)
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
        logger.info(f"Chat action: {event.action_message} in chat {event.chat_id}")
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
    # Run the main function
    asyncio.run(main()) 