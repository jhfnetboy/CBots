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

# Version
VERSION = "0.23.8"

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
        channel_input = data.get('channel_id')  # 格式: Account_Abstraction_Community/18472
        scheduled_time = data.get('scheduled_time')
        
        logger.info(f"Received request - Message: {message}, Channel: {channel_input}")
        
        if not message or not channel_input:
            return jsonify({'error': 'Missing message or channel input'}), 400
            
        # 处理频道ID
        try:
            # 从 Account_Abstraction_Community/18472 格式中提取数字
            parts = str(channel_input).split('/')
            logger.info(f"Split channel input into parts: {parts}")
            
            if len(parts) < 2:
                raise ValueError("Invalid format")
            channel_number = parts[-1].strip()
            logger.info(f"Extracted channel number: {channel_number}")
            
            # 尝试不同的ID格式
            channel_id = int(channel_number)  # 原始ID
            channel_id_with_prefix = int(f"-100{channel_number}")  # 带-100前缀的ID
            logger.info(f"Channel ID formats - Original: {channel_id}, With prefix: {channel_id_with_prefix}")
        except (IndexError, ValueError) as e:
            logger.error(f"Failed to extract channel ID: {str(e)}")
            return jsonify({'error': 'Invalid channel input format. Please use format: Account_Abstraction_Community/18472'}), 400
            
        # Log the message
        logger.info(f"Sending message to channel {channel_id}: {message}")
        
        # Get client from app context
        client = web_bp.client
        
        # Create async task for sending message
        async def send_async():
            try:
                # 尝试不同的方法获取实体
                try:
                    # 方法1: 使用原始ID
                    logger.info(f"Attempting to get entity with original ID: {channel_id}")
                    peer = PeerChannel(channel_id=channel_id)
                    entity = await client.get_entity(peer)
                    logger.info(f"Successfully got entity using original ID: {channel_id}")
                except Exception as e1:
                    logger.error(f"Failed to get entity with original ID: {str(e1)}")
                    try:
                        # 方法2: 使用带前缀的ID
                        logger.info(f"Attempting to get entity with prefixed ID: {channel_id_with_prefix}")
                        peer = PeerChannel(channel_id=channel_id_with_prefix)
                        entity = await client.get_entity(peer)
                        logger.info(f"Successfully got entity using prefixed ID: {channel_id_with_prefix}")
                    except Exception as e2:
                        logger.error(f"Failed to get entity with prefixed ID: {str(e2)}")
                        try:
                            # 方法3: 使用InputPeerChannel
                            logger.info(f"Attempting to get entity with InputPeerChannel: {channel_id}")
                            peer = InputPeerChannel(channel_id=channel_id, access_hash=0)
                            entity = await client.get_entity(peer)
                            logger.info(f"Successfully got entity using InputPeerChannel: {channel_id}")
                        except Exception as e3:
                            logger.error(f"Failed to get entity with InputPeerChannel: {str(e3)}")
                            raise
                
                # Send message using the entity
                await client.send_message(entity, message)
                logger.info(f"Message sent successfully to {channel_id}")
                
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