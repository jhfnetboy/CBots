import os
import json
import logging
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from telethon import TelegramClient, events
from command_manager import CommandManager
from bot_handlers import BotHandlers
from dotenv import load_dotenv

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

@app.route('/')
def index():
    """Root endpoint"""
    return render_template('telegram.html')

@app.route('/api/send_message', methods=['POST'])
async def send_message():
    """Send message endpoint"""
    try:
        data = await request.get_json()
        message = data.get('message')
        channel_id = data.get('channel_id')
        scheduled_time = data.get('scheduled_time')
        
        if not message or not channel_id:
            return jsonify({'error': 'Missing message or channel_id'}), 400
        
        client = app.config['client']
        
        # Get actual chat ID from environment variable
        chat_id = os.getenv(channel_id)
        if not chat_id:
            return jsonify({'error': f'Channel ID {channel_id} not found'}), 404
            
        # Log the message
        logger.info(f"Sending message to channel {channel_id}: {message}")
        
        if scheduled_time:
            # Handle scheduled message
            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            now = datetime.now()
            delay = (scheduled_datetime - now).total_seconds()
            
            if delay > 0:
                await asyncio.sleep(delay)
                
        await client.send_message(chat_id, message)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
    app.config['client'] = client
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