from flask import Blueprint, request, jsonify, render_template
import logging
import asyncio
from datetime import datetime
import os
from telethon.utils import get_peer_id
from telethon.tl.types import PeerChannel, InputPeerChannel
from telethon.errors import ChannelPrivateError
from telegram_core import TelegramCore
from twitter_core import TwitterCore
from telegram_api import TelegramAPI
from twitter_api import TwitterAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
web_bp = Blueprint('web', __name__)

# Store the main event loop
main_loop = None
telegram_api = None
twitter_api = None

# Version
VERSION = "0.23.12"

def set_main_loop(loop):
    """Set the main event loop"""
    global main_loop
    main_loop = loop

def init_web_routes(app, telegram_client):
    """Initialize web routes with the Flask app and Telegram client"""
    global telegram_api, twitter_api
    
    # 初始化 API 实例
    telegram_core = TelegramCore()
    telegram_core.client = telegram_client
    telegram_api = TelegramAPI(core=telegram_core)
    
    twitter_core = TwitterCore()
    twitter_api = TwitterAPI(core=twitter_core)
    
    # 注册蓝图
    app.register_blueprint(web_bp)

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
            
        # 使用主事件循环
        if not main_loop:
            logger.error("Main event loop not initialized")
            return jsonify({'error': 'Server not ready'}), 500
            
        async def send_async():
            try:
                # 发送消息
                result = await telegram_api.send_message(
                    message=message,
                    channel=community_name,
                    topic_id=topic_id,
                    scheduled_time=scheduled_time
                )
                return result
            except Exception as e:
                logger.error(f"Error in send_async: {str(e)}")
                return {'error': str(e)}
                
        # 使用 run_coroutine_threadsafe 在主事件循环中执行异步操作
        future = asyncio.run_coroutine_threadsafe(send_async(), main_loop)
        try:
            result = future.result(timeout=30)  # 设置30秒超时
            if 'error' in result:
                logger.error(f"Error sending message: {result['error']}")
                return jsonify(result), 500
            return jsonify(result)
        except asyncio.TimeoutError:
            logger.error("Timeout while sending message")
            return jsonify({'error': 'Timeout while sending message'}), 500
        except Exception as e:
            logger.error(f"Error executing send_async: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        return jsonify({'error': str(e)}), 500 