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

@web_bp.route('/twitter')
def twitter():
    """Twitter bot page"""
    return render_template('twitter.html', version=VERSION)

@web_bp.route('/telegram')
def telegram():
    """Telegram bot page"""
    return render_template('telegram.html', version=VERSION)

@web_bp.route('/api/send_message', methods=['POST'])
def send_message():
    """Send message endpoint"""
    try:
        data = request.get_json()
        channel = data.get('channel')
        message = data.get('message')
        scheduled_time = data.get('scheduled_time')
        
        logger.info(f"Received send_message request - Channel: {channel}, Message: {message}, Scheduled: {scheduled_time}")
        
        if not channel or not message:
            logger.error("Missing channel or message in request")
            return jsonify({'error': 'Channel and message are required'}), 400
            
        # Extract community name and topic ID from input format: "Account_Abstraction_Community/2817"
        try:
            community_name, topic_id = channel.split('/')
            topic_id = int(topic_id)
            logger.info(f"Extracted community name: {community_name}, topic ID: {topic_id}")
        except ValueError as e:
            logger.error(f"Invalid channel format: {channel}, Error: {str(e)}")
            return jsonify({'error': 'Invalid channel format. Use format: CommunityName/TopicID'}), 400
            
        # Get client from blueprint
        client = web_bp.client
        if not client:
            logger.error("Telegram client not initialized")
            return jsonify({'error': 'Telegram client not initialized'}), 500
            
        # 获取群组实体
        logger.info(f"Attempting to get entity for community: {community_name}")
        try:
            community = client.loop.run_until_complete(client.get_entity(community_name))
            logger.info(f"Found group: {community.title} (ID: {community.id})")
        except Exception as e:
            logger.error(f"Failed to get community entity: {str(e)}")
            return jsonify({'error': f'Failed to get community: {str(e)}'}), 500
            
        if scheduled_time:
            # Convert scheduled_time to datetime
            schedule_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            # Wait until scheduled time
            now = datetime.utcnow()
            if schedule_dt > now:
                delay = (schedule_dt - now).total_seconds()
                logger.info(f"Scheduling message for {schedule_dt} (delay: {delay}s)")
                # 使用主事件循环调度消息
                if main_loop is None:
                    logger.error("Main loop not set for scheduled messages")
                    return jsonify({'error': 'Server not ready for scheduled messages'}), 500
                future = asyncio.run_coroutine_threadsafe(
                    client.send_message(community, message, reply_to=topic_id),
                    main_loop
                )
                logger.info("Message scheduled successfully")
                return jsonify({'success': True, 'scheduled': True})
        
        # 发送消息
        logger.info(f"Attempting to send message to topic {topic_id}")
        logger.info(f"Message content: {message}")
        
        try:
            # 使用客户端的事件循环发送消息
            response = client.loop.run_until_complete(
                client.send_message(community, message, reply_to=topic_id)
            )
            logger.info(f"Message sent successfully! Message ID: {response.id}")
            return jsonify({'success': True, 'message_id': response.id})
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        return jsonify({'error': str(e)}), 500

def init_web_routes(app, client):
    """Initialize web routes with the Flask app and Telegram client"""
    web_bp.client = client
    app.register_blueprint(web_bp) 