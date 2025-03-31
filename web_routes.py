from flask import Blueprint, request, jsonify, render_template
import logging
import asyncio
from datetime import datetime
import os
from telethon.utils import get_peer_id
from telethon.tl.types import PeerChannel, InputPeerChannel
from telethon.errors import ChannelPrivateError
from telegram_core import TelegramCore
from twitter_core import TwitterCore
from telegram_api import TelegramAPI
from twitter_api import TwitterAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
web_bp = Blueprint('web', __name__)

# Store the main event loop
main_loop = None
telegram_api = None
twitter_api = None

# Version
VERSION = "0.23.26"

def set_main_loop(loop):
    """Set the main event loop"""
    global main_loop
    main_loop = loop
    print("\033[92m" + f"Bot Version: {VERSION}" + "\033[0m")  # 绿色显示版本号

def init_web_routes(app, telegram_client):
    """Initialize web routes with the Flask app and Telegram client"""
    global telegram_api, twitter_api
    
    # 获取环境变量
    mode = os.environ.get('MODE', 'dev')
    if mode == 'prd':
        logger.info("Running in production mode on port 8872")
    else:
        logger.info("Running in development mode on port 8873")
    
    # 初始化 API 实例
    telegram_core = TelegramCore()
    telegram_core.client = telegram_client
    telegram_api = TelegramAPI(core=telegram_core)
    
    twitter_core = TwitterCore()
    twitter_api = TwitterAPI(core=twitter_core)
    
    # 注册蓝图
    app.register_blueprint(web_bp)

@web_bp.route('/')
def index():
    """Root endpoint"""
    return render_template('telegram.html')

@web_bp.route('/twitter')
def twitter():
    """Twitter bot page"""
    return render_template('twitter.html')

@web_bp.route('/telegram')
def telegram():
    """Telegram bot page"""
    return render_template('telegram.html')

@web_bp.route('/api/send_message', methods=['POST'])
def send_message():
    """Send message endpoint"""
    try:
        data = request.get_json()
        logger.info(f"Raw request data: {data}")
        
        channel = data.get('channel')
        message = data.get('message')
        scheduled_time = data.get('scheduled_time')
        image_data = data.get('image')  # Base64 encoded image data
        image_url = data.get('image_url')  # URL to an image
        
        logger.info(f"Parsed request data - Channel: {channel}, Message: {message}, Scheduled time type: {type(scheduled_time)}, Scheduled value: {scheduled_time}, Has Image: {bool(image_data)}, Has Image URL: {bool(image_url)}")
        
        if not channel or (not message and not image_data and not image_url):
            logger.error("Missing channel or message/image in request")
            return jsonify({'error': 'Channel and message/image are required'}), 400
            
        # 处理不同格式的Telegram链接
        try:
            community_name = None
            topic_id = None
            
            # 预处理：去除前后空格
            channel = channel.strip()
            logger.info(f"Channel after stripping whitespace: '{channel}'")
            
            # 格式1: Account_Abstraction_Community/18472
            if '/' in channel and not channel.startswith('http'):
                community_name, topic_id = channel.split('/')
                topic_id = int(topic_id)
                logger.info(f"Format 1: Extracted community name: {community_name}, topic ID: {topic_id}")
            # 格式2: https://t.me/c/1807106448/33
            elif channel.startswith('https://t.me/c/'):
                parts = channel.replace('https://t.me/c/', '').split('/')
                if len(parts) == 2:
                    community_name = parts[0]  # 这里是数字ID
                    topic_id = int(parts[1])
                    # 私有频道需要处理成整数ID
                    community_name = int(community_name)
                    logger.info(f"Format 2: Extracted channel ID: {community_name}, topic ID: {topic_id}")
            # 格式3: https://t.me/ETHPandaOrg/25
            elif channel.startswith('https://t.me/'):
                parts = channel.replace('https://t.me/', '').split('/')
                if len(parts) == 2:
                    community_name = parts[0]  # 这里是用户名
                    topic_id = int(parts[1])
                    logger.info(f"Format 3: Extracted channel username: {community_name}, topic ID: {topic_id}")
            else:
                raise ValueError(f"Unsupported channel format: {channel}")
                
            if community_name is None or topic_id is None:
                raise ValueError(f"Failed to parse channel format: {channel}")
                
            logger.info(f"Final parsed values - community_name: {community_name}, topic_id: {topic_id}")
        except ValueError as e:
            logger.error(f"Invalid channel format: {channel}, Error: {str(e)}")
            return jsonify({'error': 'Invalid channel format. Supported formats: CommunityName/TopicID, https://t.me/c/ChannelID/MessageID, or https://t.me/Username/MessageID'}), 400
            
        # 使用主事件循环
        if not main_loop:
            logger.error("Main event loop not initialized")
            return jsonify({'error': 'Server not ready'}), 500
        
        logger.info(f"Before send_async - scheduled_time type: {type(scheduled_time)}, value: {scheduled_time}")
            
        async def send_async():
            try:
                logger.info(f"Inside send_async - scheduled_time type: {type(scheduled_time)}, value: {scheduled_time}")
                
                # 确保在使用前检查变量是否存在
                _scheduled_time = scheduled_time  # 创建一个本地变量
                logger.info(f"Local _scheduled_time variable created: {_scheduled_time}")
                
                # 如果是定时发送
                if _scheduled_time:
                    logger.info(f"Processing scheduled message with time: {_scheduled_time}")
                    try:
                        _scheduled_time = _scheduled_time.replace('Z', '')
                        scheduled_datetime = datetime.fromisoformat(_scheduled_time)
                        now = datetime.now()
                        
                        if scheduled_datetime <= now:
                            logger.error("Scheduled time is in the past")
                            return jsonify({'error': 'Scheduled time must be in the future'}), 400
                            
                        delay = (scheduled_datetime - now).total_seconds()
                        days = int(delay // (24 * 3600))
                        hours = int((delay % (24 * 3600)) // 3600)
                        minutes = int((delay % 3600) // 60)
                        
                        delay_info = {
                            'days': days,
                            'hours': hours,
                            'minutes': minutes,
                            'total_seconds': delay
                        }
                        logger.info(f"Message scheduled for {delay_info}")
                        
                        # 发送定时消息
                        logger.info(f"Calling telegram_api.send_message with scheduled time: {_scheduled_time}")
                        result = await telegram_api.send_message(
                            message=message,
                            channel=community_name,
                            topic_id=topic_id,
                            scheduled_time=_scheduled_time,
                            image_data=image_data,
                            image_url=image_url
                        )
                        
                        if 'status' in result and result['status'] == 'scheduled':
                            result['scheduled_info'] = {
                                'delay': delay_info,
                                'scheduled_time': scheduled_datetime.isoformat(),
                                'current_time': now.isoformat()
                            }
                        return result
                        
                    except ValueError as e:
                        logger.error(f"Invalid scheduled time format: {_scheduled_time}")
                        return jsonify({'error': f'Invalid scheduled time format: {str(e)}'}), 400
                else:
                    # 直发消息
                    logger.info("Sending immediate message - scheduled_time is empty or None")
                    return await telegram_api.send_message(
                        message=message,
                        channel=community_name,
                        topic_id=topic_id,
                        scheduled_time=None,
                        image_data=image_data,
                        image_url=image_url
                    )
                    
            except Exception as e:
                logger.error(f"Error in send_async: {str(e)}")
                import traceback
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return {'error': str(e)}
        
        logger.info("Creating asyncio task with run_coroutine_threadsafe")
                
        # 使用 run_coroutine_threadsafe 在主事件循环中执行异步操作
        future = asyncio.run_coroutine_threadsafe(send_async(), main_loop)
        try:
            logger.info("Waiting for future result with timeout")
            result = future.result(timeout=30)  # 设置30秒超时
            logger.info(f"Future result received: {result}")
            
            if isinstance(result, tuple) and len(result) == 2:
                return result[0], result[1]
            if 'error' in result:
                logger.error(f"Error sending message: {result['error']}")
                return jsonify(result), 500
            return jsonify(result)
        except asyncio.TimeoutError:
            logger.error("Timeout while sending message")
            return jsonify({'error': 'Timeout while sending message'}), 500
        except Exception as e:
            logger.error(f"Error executing send_async: {str(e)}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/send_tweet', methods=['POST'])
def send_tweet():
    """Send tweet endpoint"""
    try:
        data = request.get_json()
        message = data.get('message')
        scheduled_time_value = data.get('scheduled_time')  # 使用不同的变量名
        image_data = data.get('image')  # Base64 encoded image data
        
        logger.info(f"Received send_tweet request - Message: {message}, Scheduled: {scheduled_time_value}, Has Image: {bool(image_data)}")
        
        if not message and not image_data:
            logger.error("Missing message/image in request")
            return jsonify({'error': 'Message or image is required'}), 400
            
        # 使用主事件循环
        if not main_loop:
            logger.error("Main event loop not initialized")
            return jsonify({'error': 'Server not ready'}), 500
            
        async def send_async():
            try:
                # 计算定时发送的延迟时间
                delay_info = None
                scheduled_datetime = None
                _scheduled_time = scheduled_time_value  # 在函数作用域内使用本地变量
                now = datetime.now()
                
                if _scheduled_time:
                    try:
                        # 解析时间字符串，移除 'Z' 后缀
                        _scheduled_time = _scheduled_time.replace('Z', '')
                        scheduled_datetime = datetime.fromisoformat(_scheduled_time)
                        
                        # 如果时间已经过去，返回错误
                        if scheduled_datetime <= now:
                            return jsonify({'error': 'Scheduled time must be in the future'}), 400
                        
                        delay = (scheduled_datetime - now).total_seconds()
                        
                        # 计算天、小时、分钟
                        days = int(delay // (24 * 3600))
                        hours = int((delay % (24 * 3600)) // 3600)
                        minutes = int((delay % 3600) // 60)
                        
                        delay_info = {
                            'days': days,
                            'hours': hours,
                            'minutes': minutes,
                            'total_seconds': delay
                        }
                        logger.info(f"Tweet scheduled for {delay_info}")
                    except ValueError as e:
                        logger.error(f"Invalid scheduled time format: {_scheduled_time}")
                        return jsonify({'error': f'Invalid scheduled time format: {str(e)}'}), 400
                
                # 发送推文
                result = await twitter_api.send_tweet(
                    message=message,
                    scheduled_time=_scheduled_time if _scheduled_time else None,
                    image_data=image_data
                )
                
                # 添加定时发送信息
                if delay_info and scheduled_datetime:
                    result['scheduled_info'] = {
                        'delay': delay_info,
                        'scheduled_time': scheduled_datetime.isoformat(),
                        'current_time': now.isoformat()
                    }
                
                return result
            except Exception as e:
                logger.error(f"Error in send_async: {str(e)}")
                return {'error': str(e)}
                
        # 使用 run_coroutine_threadsafe 在主事件循环中执行异步操作
        future = asyncio.run_coroutine_threadsafe(send_async(), main_loop)
        try:
            result = future.result(timeout=30)  # 设置30秒超时
            if isinstance(result, tuple) and len(result) == 2:
                return result[0], result[1]
            if 'error' in result:
                logger.error(f"Error sending tweet: {result['error']}")
                return jsonify(result), 500
            return jsonify(result)
        except asyncio.TimeoutError:
            logger.error("Timeout while sending tweet")
            return jsonify({'error': 'Timeout while sending tweet'}), 500
        except Exception as e:
            logger.error(f"Error executing send_async: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        logger.error(f"Error in send_tweet: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@web_bp.route('/api/version')
def get_version():
    """Get version endpoint"""
    return jsonify({'version': VERSION}) 