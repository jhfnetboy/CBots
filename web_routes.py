from flask import Blueprint, request, jsonify, render_template
import logging
import asyncio
from datetime import datetime
import os

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
web_bp = Blueprint('web', __name__)

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
            if scheduled_time:
                scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                now = datetime.now()
                delay = (scheduled_datetime - now).total_seconds()
                
                if delay > 0:
                    await asyncio.sleep(delay)
            
            await client.send_message(chat_id, message)
        
        # Run the async task
        asyncio.run(send_async())
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': str(e)}), 500

def init_web_routes(app, client):
    """Initialize web routes with the Flask app and Telegram client"""
    web_bp.client = client
    app.register_blueprint(web_bp) 