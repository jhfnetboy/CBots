import logging
from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import asyncio
import threading
from telegram_api import TelegramAPI
from twitter_api import TwitterAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Version
VERSION = "0.23.2"

# API configuration
API_BASE_URL = "http://127.0.0.1:5000/api"

def run_async(coro):
    """Run coroutine in a new event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/')
def index():
    """Root endpoint"""
    return render_template('telegram.html', version=VERSION)

@app.route('/twitter')
def twitter():
    """Twitter bot page"""
    return render_template('twitter.html', version=VERSION)

@app.route('/telegram')
def telegram():
    """Telegram bot page"""
    return render_template('telegram.html', version=VERSION)

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
                    
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 运行异步函数
                result = loop.run_until_complete(
                    self.telegram_api.send_message(data['message'])
                )
                
                # 关闭事件循环
                loop.close()
                
                return jsonify(result)
            except Exception as e:
                logging.error(f"Error sending message: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 运行异步函数
                result = loop.run_until_complete(
                    self.telegram_api.get_status()
                )
                
                # 关闭事件循环
                loop.close()
                
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
                    
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 运行异步函数
                result = loop.run_until_complete(
                    self.twitter_api.send_tweet(
                        data['message'],
                        data.get('scheduled_time')
                    )
                )
                
                # 关闭事件循环
                loop.close()
                
                return jsonify(result)
            except Exception as e:
                logging.error(f"Error sending tweet: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/twitter/status', methods=['GET'])
        def get_twitter_status():
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 运行异步函数
                result = loop.run_until_complete(
                    self.twitter_api.get_status()
                )
                
                # 关闭事件循环
                loop.close()
                
                return jsonify(result)
            except Exception as e:
                logging.error(f"Error getting Twitter status: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
    def run_web_service(self, host='0.0.0.0', port=8872):
        self.app.run(host=host, port=port) 