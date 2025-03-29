from flask import Flask, request, jsonify
import asyncio
from telegram_core import TelegramCore
from twitter_core import TwitterCore
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotAPI:
    def __init__(self, telegram_core, twitter_core):
        self.app = Flask(__name__)
        self.telegram_core = telegram_core
        self.twitter_core = twitter_core
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/api/telegram/send_message', methods=['POST'])
        def send_telegram_message():
            try:
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({'error': 'Message is required'}), 400
                    
                # 创建事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.telegram_core.send_message(
                            data['message'],
                            data.get('channel'),
                            data.get('topic_id'),
                            data.get('scheduled_time')
                        )
                    )
                finally:
                    loop.close()
                
                if 'error' in result:
                    return jsonify(result), 500
                    
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error sending Telegram message: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/twitter/send_tweet', methods=['POST'])
        def send_tweet():
            try:
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({'error': 'Message is required'}), 400
                    
                # 创建事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.twitter_core.send_tweet(
                            data['message'],
                            data.get('scheduled_time')
                        )
                    )
                finally:
                    loop.close()
                
                if 'error' in result:
                    return jsonify(result), 500
                    
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error sending tweet: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/telegram/status', methods=['GET'])
        def get_telegram_status():
            try:
                # 创建事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.telegram_core.get_status()
                    )
                finally:
                    loop.close()
                
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error getting Telegram status: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/twitter/status', methods=['GET'])
        def get_twitter_status():
            try:
                # 创建事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.twitter_core.get_status()
                    )
                finally:
                    loop.close()
                
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error getting Twitter status: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
    def run(self, host='127.0.0.1', port=8871):
        """启动API服务"""
        self.app.run(host=host, port=port) 