import os
import json
import logging
import asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from command_manager import CommandManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize command manager
command_manager = CommandManager()

# Initialize Telegram client
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

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
        
        await client.send_message(chat_id, message)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@client.on(events.NewMessage(pattern=lambda e: not e.message.text.startswith('/')))
async def handle_message(event):
    try:
        # Get response from command manager
        response = await command_manager.handle_message(event.message.text)
        
        # Send response back to user
        await event.reply(response)
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await event.reply("Sorry, there was an error processing your message.")

if __name__ == '__main__':
    with client:
        app.run(host='0.0.0.0', port=5001) 