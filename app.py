import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from command_manager import CommandManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize command manager
command_manager = CommandManager()

# Initialize Telegram client
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
PORT = int(os.getenv('PORT', 8872))
DEFAULT_GROUP_ID = int(os.getenv('DEFAULT_GROUP_ID', 1))  # 默认群组ID

# Store muted users and their unmute times
muted_users = {}

def create_client():
    """Create and return a new TelegramClient instance"""
    return TelegramClient('bot', api_id, api_hash)

async def init_client(client):
    """Initialize the client with bot token"""
    await client.start(bot_token=bot_token)
    return client

async def send_online_message(client):
    """Send online message to default group"""
    try:
        message = "Hi，COS72 Bot is online now。/help了解更多。"
        await client.send_message(DEFAULT_GROUP_ID, message)
        logger.info(f"Sent online message to group {DEFAULT_GROUP_ID}")
    except Exception as e:
        logger.error(f"Error sending online message: {str(e)}")

async def send_daily_password(client):
    """Send daily password to default group"""
    try:
        password = os.getenv('DAILY_PASSWORD', '')
        await client.send_message(DEFAULT_GROUP_ID, f"今日密码：{password}")
        logger.info(f"Sent daily password to group {DEFAULT_GROUP_ID}")
    except Exception as e:
        logger.error(f"Error sending daily password: {str(e)}")

async def schedule_tasks(client):
    """Schedule daily tasks"""
    while True:
        now = datetime.now()
        if now.hour == 9:  # 9:00 AM
            await send_daily_password(client)
        
        # Check for users to unmute
        for user_id, unmute_time in list(muted_users.items()):
            if datetime.now() >= unmute_time:
                try:
                    await client.edit_permissions(DEFAULT_GROUP_ID, user_id, send_messages=True)
                    del muted_users[user_id]
                    logger.info(f"Unmuted user {user_id}")
                except Exception as e:
                    logger.error(f"Error unmuting user {user_id}: {str(e)}")
        
        await asyncio.sleep(60)  # Check every minute

# Initialize Flask app
app = Flask(__name__)

@app.route('/send_message', methods=['POST'])
async def send_message():
    try:
        data = await request.get_json()
        message = data.get('message')
        chat_id = data.get('chat_id')
        
        if not message or not chat_id:
            return jsonify({'error': 'Missing message or chat_id'}), 400
        
        client = app.config['client']
        await client.send_message(chat_id, message)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': str(e)}), 500

def setup_handlers(client):
    """Set up event handlers for the client"""
    
    @client.on(events.NewMessage(pattern=lambda e: not e.message.text.startswith('/')))
    async def handle_message(event):
        try:
            # Log the message
            logger.info(f"Received message from {event.sender_id}: {event.message.text}")
            
            # Check if user is muted
            if event.sender_id in muted_users:
                await event.reply("您当前处于禁言状态，请私聊机器人发送每日密码以解除禁言。")
                return
            
            # Get response from command manager
            response = await command_manager.handle_message(event.message.text)
            
            # Send response back to user
            await event.reply(response)
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await event.reply("Sorry, there was an error processing your message.")

    @client.on(events.ChatAction)
    async def handle_new_member(event):
        """Handle new member joins"""
        try:
            if event.user_joined:
                user_id = event.user_id
                # Mute user in default group
                await client.edit_permissions(DEFAULT_GROUP_ID, user_id, send_messages=False)
                logger.info(f"Muted user {user_id} in group {DEFAULT_GROUP_ID}")
                
                # Store unmute time (24 hours from now)
                muted_users[user_id] = datetime.now() + timedelta(hours=24)
                
                # Send welcome message
                await event.reply(f"欢迎新成员！请在24小时内私聊机器人发送每日密码以解除禁言。")
        except Exception as e:
            logger.error(f"Error handling new member: {str(e)}")

    @client.on(events.NewMessage(func=lambda e: e.is_private))
    async def handle_private_message(event):
        """Handle private messages"""
        try:
            user_id = event.sender_id
            message_text = event.message.text
            
            # Check if user is muted
            if user_id in muted_users:
                # Check if message is the daily password
                if message_text == os.getenv('DAILY_PASSWORD', ''):
                    # Unmute user in default group
                    await client.edit_permissions(DEFAULT_GROUP_ID, user_id, send_messages=True)
                    logger.info(f"Unmuted user {user_id} in group {DEFAULT_GROUP_ID}")
                    
                    # Update unmute time to 1 hour from now
                    muted_users[user_id] = datetime.now() + timedelta(hours=1)
                    
                    await event.reply("密码正确！您的禁言将在1小时后解除。")
                else:
                    await event.reply("密码错误，请重试。")
        except Exception as e:
            logger.error(f"Error handling private message: {str(e)}")

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
    await send_online_message(client)
    
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