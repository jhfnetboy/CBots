import logging
from flask import Flask, render_template, request, jsonify
import asyncio
from telegram_api import TelegramAPI
from twitter_api import TwitterAPI
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "0.23.5"

class WebService:
    def __init__(self, telegram_api, twitter_api):
        self.app = Flask(__name__)
        self.telegram_api = telegram_api
        self.twitter_api = twitter_api
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            """Root endpoint"""
            return render_template('telegram.html', version=VERSION)
            
        @self.app.route('/telegram')
        def telegram():
            """Telegram bot page"""
            return render_template('telegram.html', version=VERSION)
            
        @self.app.route('/api/send_message', methods=['POST'])
        def send_message():
            try:
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({'error': 'Message is required'}), 400
                    
                # 使用主事件循环
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    self.telegram_api.send_message(
                        data['message'],
                        data.get('channel'),
                        data.get('topic_id'),
                        data.get('scheduled_time')
                    )
                )
                
                if 'error' in result:
                    return jsonify(result), 500
                    
                return jsonify(result)
            except Exception as e:
                logging.error(f"Error sending message: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            try:
                # 使用主事件循环
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    self.telegram_api.get_status()
                )
                
                return jsonify(result)
            except Exception as e:
                logging.error(f"Error getting status: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/twitter')
        def twitter():
            """Twitter bot page"""
            return render_template('twitter.html', version=VERSION)
            
        @self.app.route('/api/send_tweet', methods=['POST'])
        def send_tweet():
            try:
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({'error': 'Message is required'}), 400
                    
                # 使用主事件循环
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    self.twitter_api.send_tweet(
                        data['message'],
                        data.get('scheduled_time')
                    )
                )
                
                if 'error' in result:
                    return jsonify(result), 500
                    
                if result.get('status') == 'scheduled':
                    return jsonify(result)
                    
                return jsonify({
                    'success': True,
                    'message': 'Tweet sent successfully',
                    'tweet_url': result
                })
            except Exception as e:
                logging.error(f"Error sending tweet: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/twitter/status', methods=['GET'])
        def get_twitter_status():
            try:
                # 使用主事件循环
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    self.twitter_api.get_status()
                )
                
                return jsonify(result)
            except Exception as e:
                logging.error(f"Error getting Twitter status: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
    def run_web_service(self, host='0.0.0.0', port=8872):
        self.app.run(host=host, port=port) 