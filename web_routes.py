from flask import Blueprint, request, jsonify, render_template
import logging
import asyncio
from datetime import datetime
import os
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
VERSION = "0.23.12"

def set_main_loop(loop):
    """Set the main event loop"""
    global main_loop
    main_loop = loop

@web_bp.route('/')
def index():
    """Root endpoint"""
    return render_template('telegram.html', version=VERSION)

@web_bp.route('/api/send_message', methods=['POST'])
def send_message():
    """Send message endpoint"""
    try:
        data = request.get_json()
        message = data.get('message')
        channel_input = data.get('channel_id')  # 格式: Account_Abstraction_Community/2817
        scheduled_time = data.get('scheduled_time')
        
        logger.info(f"Received request - Message: {message}, Channel: {channel_input}")
        
        if not message or not channel_input:
            return jsonify({'error': 'Missing message or channel input'}), 400
            
        # 处理频道输入
        try:
            # 从 Account_Abstraction_Community/2817 格式中提取社区名称和话题ID
            parts = str(channel_input).split('/')
            logger.info(f"Split channel input into parts: {parts}")
            
            if len(parts) < 2:
                raise ValueError("Invalid format")
                
            community_name = parts[0].strip()
            topic_id = int(parts[1].strip())
            
            logger.info(f"Extracted community name: {community_name}, topic ID: {topic_id}")
            
        except (IndexError, ValueError) as e:
            logger.error(f"Failed to extract community name and topic ID: {str(e)}")
            return jsonify({'error': 'Invalid channel input format. Please use format: Account_Abstraction_Community/2817'}), 400
            
        # Get client from app context
        client = web_bp.client
        
        # Create async task for sending message
        async def send_async():
            try:
                # 获取社区实体
                community_entity = await client.get_entity(community_name)
                logger.info(f"Got community entity: {community_entity.id}")
                
                # 发送消息到话题
                sent_message = await client.send_message(
                    entity=community_entity,
                    message=message,
                    reply_to=topic_id
                )
                logger.info(f"Message sent successfully to topic {topic_id}")
                
                # Handle scheduled message if needed
                if scheduled_time:
                    scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                    now = datetime.now()
                    delay = (scheduled_datetime - now).total_seconds()
                    
                    if delay > 0:
                        logger.info(f"Message scheduled for {scheduled_datetime}")
                        await asyncio.sleep(delay)
                        await client.send_message(
                            entity=community_entity,
                            message=f"[Scheduled Message] {message}",
                            reply_to=topic_id
                        )
                        logger.info(f"Scheduled message sent to topic {topic_id}")
                        
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