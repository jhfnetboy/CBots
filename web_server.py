from flask import Flask, render_template, request, jsonify
import logging
from config import WEB_SERVER_CONFIG
from bot import TelegramBot
from twitter_bot import TwitterBot
from channel_manager import ChannelManager
import asyncio
import threading

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

@app.route('/')
def index():
    logger.info("Accessing index page")
    return render_template('index.html')

@app.route('/twitter')
def twitter():
    logger.info("Accessing Twitter page")
    return render_template('twitter.html')

@app.route('/api/channels', methods=['GET'])
async def get_channels():
    logger.info("Received request for channels")
    try:
        if not channel_manager or not channel_manager.is_initialized:
            logger.error("Channel manager not initialized")
            return jsonify({'error': 'Channel list not initialized'}), 500
        
        channels = channel_manager.get_channels()
        logger.info(f"Returning {len(channels)} channels")
        return jsonify(channels)
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send', methods=['POST'])
async def send_message():
    try:
        if not telegram_bot:
            return jsonify({'error': 'Bot not initialized'}), 500
        
        data = request.get_json()
        message = data.get('message')
        target = data.get('target')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        await telegram_bot.send_message(message, target)
        return jsonify({'message': 'Message sent successfully'})
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'error': str(e)}), 500

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

def init_bots():
    global telegram_bot, twitter_bot, channel_manager
    
    try:
        # Start Telegram bot
        logger.info("Starting Telegram bot...")
        telegram_bot = TelegramBot()
        
        # Initialize channel manager
        logger.info("Initializing channel manager...")
        channel_manager = ChannelManager(telegram_bot)
        
        # Start Twitter bot
        logger.info("Starting Twitter bot...")
        twitter_bot = TwitterBot()
        
        logger.info("All bots initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing bots: {e}")
        raise

def run_flask():
    logger.info(f"Starting Flask server on {WEB_SERVER_CONFIG['host']}:{WEB_SERVER_CONFIG['port']}")
    try:
        app.run(
            host=WEB_SERVER_CONFIG['host'],
            port=WEB_SERVER_CONFIG['port'],
            debug=WEB_SERVER_CONFIG['debug']
        )
    except Exception as e:
        logger.error(f"Error starting Flask server: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        # Initialize bots
        init_bots()
        
        # Run Flask app
        run_flask()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise 