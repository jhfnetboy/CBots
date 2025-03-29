import logging
from flask import Flask, request, jsonify
from functools import wraps
import os
from telegram_core import TelegramCore
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
telegram_core = None

def check_local_ip(f):
    """Decorator to check if request is from localhost"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.remote_addr not in ['127.0.0.1', 'localhost']:
            return jsonify({'error': 'Access denied. Only local requests are allowed.'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/send_message', methods=['POST'])
@check_local_ip
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
            
        async def send_async():
            try:
                # 获取群组实体
                logger.info(f"Attempting to get entity for community: {community_name}")
                community = await telegram_core.client.get_entity(community_name)
                logger.info(f"Found group: {community.title} (ID: {community.id})")
                
                if scheduled_time:
                    # Convert scheduled_time to datetime
                    schedule_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                    # Wait until scheduled time
                    now = datetime.utcnow()
                    if schedule_dt > now:
                        delay = (schedule_dt - now).total_seconds()
                        logger.info(f"Scheduling message for {schedule_dt} (delay: {delay}s)")
                        await asyncio.sleep(delay)
                
                # 发送消息
                logger.info(f"Attempting to send message to topic {topic_id}")
                logger.info(f"Message content: {message}")
                
                response = await telegram_core.client.send_message(
                    community,
                    message,
                    reply_to=topic_id
                )
                logger.info(f"Message sent successfully! Message ID: {response.id}")
                return {'success': True, 'message_id': response.id}
                
            except Exception as e:
                logger.error(f"Error in send_async: {str(e)}")
                return {'error': str(e)}
        
        if scheduled_time:
            # Schedule the message
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(send_async(), loop)
            logger.info("Message scheduled successfully")
            return jsonify({'success': True, 'scheduled': True})
        else:
            # Send immediately
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(send_async(), loop)
            response = future.result(timeout=30)
            if 'error' in response:
                return jsonify(response), 500
            return jsonify(response)
            
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
@check_local_ip
def get_status():
    """Get bot status endpoint"""
    try:
        if telegram_core and telegram_core.client:
            return jsonify({
                'status': 'running',
                'daily_password': telegram_core.daily_password
            })
        return jsonify({'status': 'not running'})
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

def init_api(telegram_core_instance):
    """Initialize API with Telegram core instance"""
    global telegram_core
    telegram_core = telegram_core_instance

def run_api(host='127.0.0.1', port=5000):
    """Run the API server"""
    app.run(host=host, port=port) 