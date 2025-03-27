from flask import Blueprint, request, jsonify, render_template
import logging
import asyncio
from datetime import datetime
import os
import threading

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
web_bp = Blueprint('web', __name__)

# Store the main event loop
main_loop = None

def set_main_loop(loop):
    """Set the main event loop"""
    global main_loop
    main_loop = loop

@web_bp.route('/')
def index():
    """Root endpoint"""
    return render_template('telegram.html')

@web_bp.route('/api/send_message', methods=['POST'])
def send_message():
    """Send message endpoint"""
    try:
        data = request.get_json()
        message = data.get('message')
        channel_id = data.get('channel_id')
        
        if not message or not channel_id:
            return jsonify({'error': 'Missing message or channel_id'}), 400
        
        # Get actual chat ID from environment variable
        chat_id = os.getenv(channel_id)
        if not chat_id:
            return jsonify({'error': f'Channel ID {channel_id} not found'}), 404
            
        # Log the message
        logger.info(f"Sending message to channel {channel_id}: {message}")
        
        # Get client from app context
        client = web_bp.client
        
        # Create async task for sending message
        async def send_async():
            try:
                # Send message directly using the channel ID
                await client.send_message(chat_id, message)
                logger.info(f"Message sent successfully to {chat_id}")
            except Exception as e:
                logger.error(f"Error in send_async: {str(e)}")
                raise
        
        # Create a future to wait for the result
        future = asyncio.run_coroutine_threadsafe(send_async(), main_loop)
        
        # Wait for the result
        future.result(timeout=30)  # 30 seconds timeout
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': str(e)}), 500

def init_web_routes(app, client):
    """Initialize web routes with the Flask app and Telegram client"""
    web_bp.client = client
    app.register_blueprint(web_bp) 