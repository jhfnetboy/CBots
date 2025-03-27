import os
import logging
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
twitter_bp = Blueprint('twitter', __name__)

# Version
VERSION = "0.23.12"

# Store the main event loop
main_loop = None

def set_main_loop(loop):
    """Set the main event loop"""
    global main_loop
    main_loop = loop
    logger.info("Main loop set for Twitter routes")

def init_twitter_client():
    """Initialize Twitter client with v2 API"""
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    
    if not all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
        raise ValueError("Missing Twitter credentials")
        
    return tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

@twitter_bp.route('/')
def index():
    """Render Twitter bot control panel"""
    return render_template('twitter.html', version=VERSION)

@twitter_bp.route('/api/send_tweet', methods=['POST'])
def send_tweet():
    """Send a tweet using Twitter API v2"""
    try:
        data = request.get_json()
        message = data.get('message')
        scheduled_time = data.get('scheduled_time')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        client = init_twitter_client()
        
        async def send_async():
            try:
                if scheduled_time:
                    # Convert scheduled_time to datetime
                    schedule_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                    # Wait until scheduled time
                    now = datetime.utcnow()
                    if schedule_dt > now:
                        delay = (schedule_dt - now).total_seconds()
                        logger.info(f"Scheduling tweet for {schedule_dt} (delay: {delay}s)")
                        await asyncio.sleep(delay)
                
                # Send tweet using v2 API
                response = client.create_tweet(text=message)
                tweet_id = response.data['id']
                logger.info(f"Tweet sent successfully! Tweet ID: {tweet_id}")
                return {'success': True, 'tweet_id': tweet_id}
                
            except Exception as e:
                logger.error(f"Error sending tweet: {str(e)}")
                return {'error': str(e)}
        
        if scheduled_time:
            if main_loop is None:
                logger.error("Main loop not set for scheduled tweets")
                return jsonify({'error': 'Server not ready for scheduled tweets'}), 500
                
            # Schedule the tweet
            future = asyncio.run_coroutine_threadsafe(send_async(), main_loop)
            logger.info("Tweet scheduled successfully")
            return jsonify({'success': True, 'scheduled': True})
        else:
            # Send immediately
            response = client.create_tweet(text=message)
            tweet_id = response.data['id']
            logger.info(f"Tweet sent successfully! Tweet ID: {tweet_id}")
            return jsonify({'success': True, 'tweet_id': tweet_id})
            
    except Exception as e:
        logger.error(f"Error in send_tweet: {str(e)}")
        return jsonify({'error': str(e)}), 500

def init_twitter_routes(app):
    """Initialize Twitter routes"""
    app.register_blueprint(twitter_bp) 