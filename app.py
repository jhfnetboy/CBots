from flask import Flask, render_template, request, jsonify
from bot_manager import BotManager
import asyncio
import logging
from config import WEB_SERVER_CONFIG
import os
import threading
import signal
import sys
from datetime import datetime
import json
from command_manager import command_manager

# Configure logging with more detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_manager = None
flask_thread = None
loop = None

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """处理所有路由"""
    logger.info(f"Handling path: {path}")
    if path == '' or path == 'telegram':
        return render_template('telegram.html')
    elif path == 'twitter':
        return render_template('twitter.html')
    elif path == 'webhook':
        return telegram_webhook()
    elif path.startswith('api/'):
        return handle_api(path)
    else:
        return render_template('telegram.html')

def handle_api(path):
    """处理 API 请求"""
    if path == 'api/channels':
        return get_channels()
    elif path == 'api/send_message':
        return send_message()
    elif path == 'api/twitter/send':
        return send_tweet()
    else:
        return jsonify({'error': 'API endpoint not found'}), 404

@app.route('/telegram')
def telegram():
    """Telegram 页面"""
    return render_template('telegram.html')

@app.route('/twitter')
def twitter():
    """Twitter 页面"""
    return render_template('twitter.html')

@app.route('/webhook', methods=['POST'])
async def telegram_webhook():
    """处理 Telegram webhook 更新"""
    try:
        logger.info("Received Telegram webhook update")
        update = request.get_json()
        
        # 验证 webhook 请求
        if not update:
            logger.error("No update data received")
            return jsonify({'error': 'No update data'}), 400
            
        # 处理消息
        if 'message' in update:
            message = update['message']
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            
            # 处理命令
            if text.startswith('/'):
                command = text.split()[0]
                await command_manager.process_command(command, 'telegram', message)
            else:
                # 处理普通消息
                await command_manager.process_message('telegram', message)
                
        logger.info("Successfully processed webhook update")
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/channels', methods=['GET'])
async def get_channels():
    logger.info("Received request for channels")
    try:
        channel_manager = bot_manager.get_channel_manager()
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
        telegram_bot = bot_manager.get_telegram_bot()
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
                message=message,
                chat_id=group,
                reply_to=int(topic_id) if topic_id else None
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
        logger.info("=== Starting Twitter Send Request ===")
        # 记录请求数据
        logger.info(f"Request data: {request.get_data()}")
        logger.info(f"Request JSON: {request.get_json()}")
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        tweet_content = data.get('tweet') or data.get('message')  # 支持两种字段名
        if not tweet_content:
            logger.error("No tweet content found in request")
            return jsonify({'error': 'No tweet content provided'}), 400

        if not bot_manager:
            logger.error("Bot manager not initialized")
            return jsonify({'error': 'Bot manager not initialized'}), 500

        twitter_bot = bot_manager.get_twitter_bot()
        if not twitter_bot:
            logger.error("Twitter bot not initialized")
            return jsonify({'error': 'Twitter bot not initialized'}), 500

        # 使用 asyncio 运行异步函数
        future = asyncio.run_coroutine_threadsafe(twitter_bot.send_tweet(tweet_content), loop)
        tweet_url = future.result()  # 等待结果并获取推文URL
        
        logger.info("=== Twitter Send Request Completed ===")
        return jsonify({
            'message': 'Tweet sent successfully',
            'tweet_url': tweet_url
        })
    except Exception as e:
        logger.error(f"Error in send_tweet route: {e}", exc_info=True)
        logger.error("=== Twitter Send Request Failed ===")
        return jsonify({'error': str(e)}), 500

def run_flask():
    """Run Flask in a separate thread"""
    logger.info("=== Starting Flask Server ===")
    logger.debug(f"Host: {WEB_SERVER_CONFIG['host']}")
    logger.debug(f"Port: {WEB_SERVER_CONFIG['port']}")
    logger.debug(f"Debug mode: {WEB_SERVER_CONFIG['debug']}")
    
    try:
        app.run(
            host=WEB_SERVER_CONFIG['host'],
            port=WEB_SERVER_CONFIG['port'],
            debug=WEB_SERVER_CONFIG['debug'],
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Flask server error: {e}", exc_info=True)
        raise

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if bot_manager:
        asyncio.run_coroutine_threadsafe(bot_manager.stop(), loop)
    sys.exit(0)

async def initialize_bots():
    """Initialize all bots"""
    global bot_manager
    try:
        logger.info("=== Initializing Bot Manager ===")
        bot_manager = BotManager()
        await bot_manager.initialize()
        logger.info("Bot Manager initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing bots: {e}", exc_info=True)
        raise

def start_app():
    """Start the Flask application"""
    global loop, flask_thread
    try:
        logger.info("=== Starting Application ===")
        
        # 设置信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.debug("Event loop created and set")
        
        # 初始化机器人
        logger.info("Initializing bots...")
        loop.run_until_complete(initialize_bots())
        
        # 在新线程中启动Flask
        logger.info("Starting Flask server in separate thread...")
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        logger.debug("Flask thread started")
        
        # 运行事件循环
        logger.info("Starting event loop...")
        loop.run_forever()
        
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        if loop:
            loop.close()
        raise
    finally:
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    logger.info("=== Application Entry Point ===")
    start_app() 