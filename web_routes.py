from flask import Blueprint, request, jsonify, render_template
import logging
import asyncio
from datetime import datetime
import os
import threading
from telethon.utils import get_peer_id
from telethon.tl.types import PeerChannel, InputPeerChannel

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
                # For channel IDs, we need to extract the actual channel ID part
                # from the -100 prefixed version
                if str(channel_id).startswith('-100'):
                    # Extract the actual channel ID by removing the -100 prefix
                    raw_channel_id = int(str(channel_id)[4:])
                else:
                    # If no prefix, just use as is
                    raw_channel_id = int(channel_id)
                
                logger.info(f"Using raw channel ID: {raw_channel_id}")
                
                # Direct approach - use the channel ID directly
                try:
                    # First attempt: Use raw_channel_id directly
                    await client.send_message(channel_id, message)
                    logger.info(f"Message sent successfully to {channel_id}")
                except Exception as e:
                    logger.error(f"First attempt failed: {str(e)}")
                    
                    # Second attempt: Try with PeerChannel
                    try:
                        peer = PeerChannel(channel_id=raw_channel_id)
                        await client.send_message(peer, message)
                        logger.info(f"Message sent successfully using PeerChannel to {raw_channel_id}")
                    except Exception as e2:
                        logger.error(f"Second attempt failed: {str(e2)}")
                        
                        # Third attempt: Try with -100 prefix as integer
                        try:
                            await client.send_message(int(f"-100{raw_channel_id}"), message)
                            logger.info(f"Message sent successfully using -100 prefix to {raw_channel_id}")
                        except Exception as e3:
                            logger.error(f"Third attempt failed: {str(e3)}")
                            raise
                
                # Handle scheduled message if needed (if we get here, one of the attempts succeeded)
                if scheduled_time:
                    scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                    now = datetime.now()
                    delay = (scheduled_datetime - now).total_seconds()
                    
                    if delay > 0:
                        logger.info(f"Message scheduled for {scheduled_datetime}")
                        await asyncio.sleep(delay)
                        # Try the same approaches for scheduled message
                        try:
                            await client.send_message(channel_id, f"[Scheduled Message] {message}")
                        except:
                            try:
                                peer = PeerChannel(channel_id=raw_channel_id)
                                await client.send_message(peer, f"[Scheduled Message] {message}")
                            except:
                                await client.send_message(int(f"-100{raw_channel_id}"), f"[Scheduled Message] {message}")
                        
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