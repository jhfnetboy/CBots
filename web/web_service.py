import logging
from flask import Flask, render_template, request, jsonify
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "0.23.6"

# Bot API 配置
BOT_API_URL = "http://127.0.0.1:8871"

class WebService:
    def __init__(self):
        self.app = Flask(__name__)
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
                    
                # 调用 bot API
                response = requests.post(
                    f"{BOT_API_URL}/api/telegram/send_message",
                    json=data
                )
                
                if response.status_code != 200:
                    return jsonify(response.json()), response.status_code
                    
                return jsonify(response.json())
            except Exception as e:
                logging.error(f"Error sending message: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            try:
                # 调用 bot API
                response = requests.get(f"{BOT_API_URL}/api/telegram/status")
                
                if response.status_code != 200:
                    return jsonify(response.json()), response.status_code
                    
                return jsonify(response.json())
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
                    
                # 调用 bot API
                response = requests.post(
                    f"{BOT_API_URL}/api/twitter/send_tweet",
                    json=data
                )
                
                if response.status_code != 200:
                    return jsonify(response.json()), response.status_code
                    
                return jsonify(response.json())
            except Exception as e:
                logging.error(f"Error sending tweet: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/twitter/status', methods=['GET'])
        def get_twitter_status():
            try:
                # 调用 bot API
                response = requests.get(f"{BOT_API_URL}/api/twitter/status")
                
                if response.status_code != 200:
                    return jsonify(response.json()), response.status_code
                    
                return jsonify(response.json())
            except Exception as e:
                logging.error(f"Error getting Twitter status: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
    def run_web_service(self, host='0.0.0.0', port=8872):
        self.app.run(host=host, port=port) 