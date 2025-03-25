from flask import Flask, render_template, request, jsonify
from bot import TelegramBot
from twitter_bot import TwitterBot
from channel_manager import ChannelManager
import asyncio
import logging
from config import WEB_SERVER_CONFIG
import os
import threading
import signal
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
telegram_bot = None
twitter_bot = None
channel_manager = None
flask_thread = None
loop = None

@app.route('/')
def index():
    logger.info("Accessing telegram page")
    return render_template('telegram.html')

@app.route('/twitter')
def twitter():
    logger.info("Accessing Twitter page")
    return render_template('twitter.html')

@app.route('/api/channels', methods=['GET'])
async def get_channels():
    logger.info("Received request for channels")
    try:
        logger.info(f"Channel manager status: initialized={channel_manager.is_initialized if channel_manager else False}")
        if not channel_manager:
            logger.error("Channel manager is None")
            return jsonify({'error': 'Channel manager not initialized'}), 500
            
        if not channel_manager.is_initialized:
            logger.error("Channel manager is not initialized")
            return jsonify({'error': 'Channel list not initialized'}), 500
        
        channels = channel_manager.get_channels()
        logger.info(f"Returning {len(channels)} channels")
        logger.debug(f"Channel details: {channels}")
        return jsonify(channels)
    except Exception as e:
        logger.error(f"Error getting channels: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_message', methods=['POST'])
async def send_message():
    try:
        if not telegram_bot:
            return jsonify({
                'status': 'error',
                'message': 'Telegram bot not initialized'
            }), 500

        data = request.json
        channel_id = data.get('channel_id')
        message = data.get('message')
        scheduled_time = data.get('scheduled_time')
        
        if not channel_id or not message:
            return jsonify({
                'status': 'error',
                'message': 'Channel ID and message are required'
            }), 400
            
        # Get channel value from environment variable
        channel_value = os.getenv(channel_id)
        if not channel_value:
            return jsonify({
                'status': 'error',
                'message': 'Channel not found'
            }), 404
            
        # Parse group and topic_id from channel_value
        group, topic_id = channel_value.split('/')
        
        if scheduled_time:
            # Convert scheduled_time to datetime
            scheduled_datetime = datetime.fromisoformat(scheduled_time)
            # Calculate delay
            delay = (scheduled_datetime - datetime.now()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
        
        # Create a future for the send_message operation
        future = asyncio.run_coroutine_threadsafe(
            telegram_bot.send_message(
                message,
                group,
                reply_to=int(topic_id)  # Add topic_id as reply_to parameter
            ),
            loop
        )
        
        # Wait for the future to complete
        await asyncio.wrap_future(future)
        
        return jsonify({
            'status': 'success',
            'message': 'Message sent successfully'
        })
        
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/twitter/send', methods=['POST'])
def send_tweet():
    try:
        if not twitter_bot:
            return jsonify({'error': 'Twitter bot not initialized'}), 500
        
        data = request.get_json()
        message = data.get('message')
        schedule_time = data.get('schedule_time')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if schedule_time:
            twitter_bot.schedule_tweet(message, schedule_time)
            return jsonify({'message': 'Tweet scheduled successfully'})
        else:
            tweet_id = twitter_bot.send_tweet(message)
            return jsonify({'message': f'Tweet sent successfully with ID: {tweet_id}'})
    except Exception as e:
        logger.error(f"Error sending tweet: {e}")
        return jsonify({'error': str(e)}), 500

async def start_bots():
    global telegram_bot, twitter_bot, channel_manager
    
    try:
        # Start Telegram bot
        logger.info("Starting Telegram bot...")
        telegram_bot = TelegramBot()
        await telegram_bot.start()
        logger.info("Telegram bot started successfully")
        
        # Initialize channel manager
        logger.info("Initializing channel manager...")
        channel_manager = ChannelManager(telegram_bot)
        logger.info("Channel manager instance created")
        
        success = await channel_manager.initialize()
        if success:
            logger.info("Channel manager initialized successfully")
            # Log the channels that were loaded
            channels = channel_manager.get_channels()
            logger.info(f"Loaded channels: {channels}")
        else:
            logger.error("Failed to initialize channel manager")
            raise Exception("Failed to initialize channel manager")
        
        # Start Twitter bot
        logger.info("Starting Twitter bot...")
        twitter_bot = TwitterBot()
        twitter_bot.start_stream()
        logger.info("Twitter bot started successfully")
        
        logger.info("All bots started successfully")
        
        # Keep the bot running
        await telegram_bot.client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Error starting bots: {e}", exc_info=True)
        raise

def run_flask():
    logger.info(f"Starting Flask server on {WEB_SERVER_CONFIG['host']}:{WEB_SERVER_CONFIG['port']}")
    try:
        # Use use_reloader=False to avoid signal handling issues
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=WEB_SERVER_CONFIG['port'],
            debug=WEB_SERVER_CONFIG['debug'],
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Error starting Flask server: {str(e)}")
        raise

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal. Cleaning up...")
    if telegram_bot:
        asyncio.run_coroutine_threadsafe(telegram_bot.stop(), loop)
    if loop:
        loop.stop()
    sys.exit(0)

if __name__ == '__main__':
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and set event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start Flask in a separate thread first
        logger.info("Starting Flask server...")
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Start bots after Flask is running
        logger.info("Starting Telegram bot...")
        loop.run_until_complete(start_bots())
        
        # Keep the main thread running
        try:
            while True:
                loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down gracefully...")
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        if loop:
            loop.close()
        logger.info("Application shutdown complete") 