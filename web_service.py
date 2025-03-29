import logging
from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Version
VERSION = "0.23.12"

# API configuration
API_BASE_URL = "http://127.0.0.1:5000/api"

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

@app.route('/api/send_message', methods=['POST'])
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
            
        # Forward request to core API
        response = requests.post(
            f"{API_BASE_URL}/send_message",
            json={
                'channel': channel,
                'message': message,
                'scheduled_time': scheduled_time
            }
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get bot status endpoint"""
    try:
        # Forward request to core API
        response = requests.get(f"{API_BASE_URL}/status")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_web_service(host='0.0.0.0', port=8080):
    """Run the web service"""
    app.run(host=host, port=port) 