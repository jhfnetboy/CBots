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
            
        # Get community entity
        try:
            # Create async function to get entity
            async def get_entity():
                logger.info(f"Attempting to get entity for community: {community_name}")
                try:
                    # 尝试直接获取实体
                    entity = await client.get_entity(community_name)
                    logger.info(f"Successfully retrieved entity: {entity.title} (ID: {entity.id})")
                    return entity
                except Exception as e:
                    logger.error(f"Error getting entity directly: {str(e)}")
                    # 尝试使用输入实体
                    try:
                        input_entity = await client.get_input_entity(community_name)
                        logger.info(f"Successfully retrieved input entity: {input_entity}")
                        return input_entity
                    except Exception as e2:
                        logger.error(f"Error getting input entity: {str(e2)}")
                        raise e2
            
            # Run the async function in the event loop
            community = asyncio.run_coroutine_threadsafe(get_entity(), main_loop).result()
            logger.info(f"Successfully retrieved community: {community.title} (ID: {community.id})")
        except Exception as e:
            logger.error(f"Failed to get community entity: {str(e)}")
            return jsonify({'error': f'Failed to get community: {str(e)}'}), 500
            
        async def send_async():
            try:
                if scheduled_time:
                    # Convert scheduled_time to datetime
                    schedule_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                    # Wait until scheduled time
                    now = datetime.utcnow()
                    if schedule_dt > now:
                        delay = (schedule_dt - now).total_seconds()
                        logger.info(f"Scheduling message for {schedule_dt} (delay: {delay}s)")
                        await asyncio.sleep(delay)
                
                logger.info(f"Attempting to send message to community {community.title} (ID: {community.id})")
                logger.info(f"Message content: {message}")
                logger.info(f"Topic ID: {topic_id}")
                
                # Send message to topic
                try:
                    # 首先尝试直接发送消息
                    logger.info("尝试直接发送消息...")
                    response = await client.send_message(
                        community,
                        message
                    )
                    logger.info(f"消息发送成功! 消息ID: {response.id}")
                    return {'success': True, 'message_id': response.id}
                except Exception as e:
                    logger.error(f"直接发送消息失败: {str(e)}")
                    logger.error(f"错误类型: {type(e)}")
                    
                    # 尝试使用 reply_to 参数
                    try:
                        logger.info("尝试使用 reply_to 参数发送消息...")
                        response = await client.send_message(
                            community,
                            message,
                            reply_to=topic_id
                        )
                        logger.info(f"消息发送成功! 消息ID: {response.id}")
                        return {'success': True, 'message_id': response.id}
                    except Exception as e2:
                        logger.error(f"使用 reply_to 参数发送消息失败: {str(e2)}")
                        logger.error(f"错误类型: {type(e2)}")
                        
                        # 尝试使用群组ID
                        try:
                            logger.info(f"尝试使用群组ID发送消息... (ID: {community.id})")
                            response = await client.send_message(
                                community.id,
                                message
                            )
                            logger.info(f"消息发送成功! 消息ID: {response.id}")
                            return {'success': True, 'message_id': response.id}
                        except Exception as e3:
                            logger.error(f"使用群组ID发送消息失败: {str(e3)}")
                            logger.error(f"错误类型: {type(e3)}")
                            raise e3
                
            except Exception as e:
                logger.error(f"发送消息时出错: {str(e)}")
                logger.error(f"错误类型: {type(e)}")
                logger.error(f"错误详情: {str(e)}")
                return {'error': str(e)}
        
        if scheduled_time:
            if main_loop is None:
                logger.error("Main loop not set for scheduled messages")
                return jsonify({'error': 'Server not ready for scheduled messages'}), 500
                
            # Schedule the message
            future = asyncio.run_coroutine_threadsafe(send_async(), main_loop)
            logger.info("Message scheduled successfully")
            return jsonify({'success': True, 'scheduled': True})
        else:
            # Send immediately
            logger.info("Attempting to send message immediately")
            try:
                response = asyncio.run_coroutine_threadsafe(send_async(), main_loop).result()
                if 'error' in response:
                    logger.error(f"Error in send_async: {response['error']}")
                    return jsonify(response), 500
                return jsonify(response)
            except Exception as e:
                logger.error(f"Error executing send_async: {str(e)}")
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