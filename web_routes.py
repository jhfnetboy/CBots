from flask import Blueprint, request, jsonify, render_template
import logging
import asyncio
from datetime import datetime
import os
import threading
from telethon.utils import get_peer_id
from telethon.tl.types import PeerChannel, InputPeerChannel
from telethon.errors import ChannelPrivateError

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
        channel_input = data.get('channel_id')  # 格式: Account_Abstraction_Community/2817
        scheduled_time = data.get('scheduled_time')
        
        if not message or not channel_input:
            return jsonify({'error': 'Missing message or channel input'}), 400
            
        # 从输入中提取频道ID
        try:
            channel_number = channel_input.split('/')[-1]
            channel_id = int(channel_number)
        except (IndexError, ValueError):
            return jsonify({'error': 'Invalid channel input format. Expected format: Account_Abstraction_Community/2817'}), 400
            
        # Log the message
        logger.info(f"Sending message to channel {channel_input}: {message}")
        
        # Get client from app context
        client = web_bp.client
        
        # Create async task for sending message
        async def send_async():
            try:
                # First try to get the entity
                try:
                    # 尝试使用带-100前缀的频道ID
                    full_channel_id = int(f"-100{channel_id}")
                    entity = await client.get_entity(full_channel_id)
                    logger.info(f"Successfully got entity for channel {full_channel_id}")
                except Exception as e:
                    logger.error(f"Failed to get entity with full ID: {str(e)}")
                    try:
                        # 尝试使用原始频道ID
                        entity = await client.get_entity(channel_id)
                        logger.info(f"Successfully got entity using original channel ID {channel_id}")
                    except Exception as e2:
                        logger.error(f"Failed to get entity with original ID: {str(e2)}")
                        raise
                
                # Send message using the entity
                await client.send_message(entity, message)
                logger.info(f"Message sent successfully to {channel_input}")
                
                # Handle scheduled message if needed
                if scheduled_time:
                    scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                    now = datetime.now()
                    delay = (scheduled_datetime - now).total_seconds()
                    
                    if delay > 0:
                        logger.info(f"Message scheduled for {scheduled_datetime}")
                        await asyncio.sleep(delay)
                        await client.send_message(entity, f"[Scheduled Message] {message}")
                        logger.info(f"Scheduled message sent to channel")
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