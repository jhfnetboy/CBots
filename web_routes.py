from flask import Blueprint, request, jsonify, render_template
import logging
import asyncio
from datetime import datetime
import os
import threading
from telethon.utils import get_peer_id
from telethon.tl.types import PeerChannel

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
        scheduled_time = data.get('scheduled_time')
        
        if not message or channel_id is None:
            return jsonify({'error': 'Missing message or channel_id'}), 400
            
        # Log the message
        logger.info(f"Sending message to channel {channel_id}: {message}")
        
        # Get client from app context
        client = web_bp.client
        
        # Create async task for sending message
        async def send_async():
            try:
                # Ensure the channel ID is a properly formatted Telegram channel ID
                # Channel IDs for large channels/groups should start with -100
                str_channel_id = str(channel_id)
                if not str_channel_id.startswith('-100'):
                    # If it doesn't start with -100, add it
                    if str_channel_id.startswith('-'):
                        str_channel_id = '-100' + str_channel_id[1:]
                    else:
                        str_channel_id = '-100' + str_channel_id
                
                # Convert to integer for Telethon
                numeric_channel_id = int(str_channel_id)
                
                # Create a proper peer channel object
                peer = PeerChannel(channel_id=numeric_channel_id)
                
                # Send message using the peer
                await client.send_message(peer, message)
                logger.info(f"Message sent successfully to {numeric_channel_id}")
                
                # Handle scheduled message if needed
                if scheduled_time:
                    scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                    now = datetime.now()
                    delay = (scheduled_datetime - now).total_seconds()
                    
                    if delay > 0:
                        logger.info(f"Message scheduled for {scheduled_datetime}")
                        await asyncio.sleep(delay)
                        await client.send_message(peer, f"[Scheduled Message] {message}")
                        logger.info(f"Scheduled message sent to {numeric_channel_id}")
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