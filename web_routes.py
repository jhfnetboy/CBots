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
import hashlib

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
# 存储最近发送消息的记录，用于防止重复发送
recent_messages = {}

# Version
VERSION = "0.23.53"

def set_main_loop(loop):
    """Set the main event loop"""
    global main_loop
    main_loop = loop
    logger.info(f"主事件循环已设置: {loop}")
    logger.info(f"主事件循环ID: {id(loop)}")
    print("\033[92m" + f"Bot Version: {VERSION}" + "\033[0m")  # 绿色显示版本号

def init_web_routes(app, telegram_client):
    """Initialize web routes with the Flask app and Telegram client"""
    global telegram_api, twitter_api
    
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
    return render_template('telegram.html', version=VERSION)

@web_bp.route('/twitter')
def twitter():
    """Twitter bot page"""
    return render_template('twitter.html', version=VERSION)

@web_bp.route('/telegram')
def telegram():
    """Telegram bot page"""
    return render_template('telegram.html', version=VERSION)

@web_bp.route('/api/send_message', methods=['POST'])
def send_message():
    """Send message endpoint"""
    try:
        # 检查主事件循环是否初始化
        global main_loop
        logger.info(f"主事件循环状态: {'已初始化' if main_loop else '未初始化'}")
        if main_loop:
            logger.info(f"主事件循环ID: {id(main_loop)}")
        else:
            logger.error("主事件循环未初始化")
            # 尝试创建一个新的事件循环
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                set_main_loop(loop)
                logger.info("已临时创建并设置新的主事件循环")
            except Exception as e:
                logger.error(f"创建临时事件循环失败: {e}")
                return jsonify({'error': 'Server not ready - event loop creation failed'}), 500

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
        
        # 生成消息唯一标识，用于防止重复发送
        message_hash = hashlib.md5(f"{channel}_{message}_{scheduled_time}_{bool(image_data)}_{image_url}".encode()).hexdigest()
        
        # 检查是否是重复发送（5秒内）
        current_time = datetime.now().timestamp()
        if message_hash in recent_messages:
            last_time = recent_messages[message_hash]
            # 如果在5秒内重复发送，则拒绝
            if current_time - last_time < 5:
                logger.warning(f"Duplicate message detected within 5 seconds: {message_hash}")
                return jsonify({'error': 'Please wait a moment before sending the same message again'}), 429
        
        # 更新最近发送记录
        recent_messages[message_hash] = current_time
        
        # 清理旧记录（保留10分钟内的）
        expired_keys = [k for k, v in recent_messages.items() if current_time - v > 600]
        for key in expired_keys:
            del recent_messages[key]
            
        # Extract community name and topic ID from input format: "Account_Abstraction_Community/2817"
        try:
            community_name, topic_id = channel.split('/')
            topic_id = int(topic_id)
            logger.info(f"Extracted community name: {community_name}, topic ID: {topic_id}")
        except ValueError as e:
            logger.error(f"Invalid channel format: {channel}, Error: {str(e)}")
            return jsonify({'error': 'Invalid channel format. Use format: CommunityName/TopicID'}), 400
            
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
        logger.info(f"当前主事件循环: {main_loop}")
        logger.info(f"事件循环状态: {'运行中' if main_loop.is_running() else '未运行'}")
        logger.info(f"事件循环已关闭: {'是' if main_loop.is_closed() else '否'}")
        
        # 如果事件循环已关闭，尝试创建新的
        if main_loop.is_closed():
            logger.error("主事件循环已关闭，尝试创建新的...")
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                set_main_loop(new_loop)
                logger.info("已创建并设置新的主事件循环")
            except Exception as e:
                logger.error(f"创建新事件循环失败: {e}")
                return jsonify({'error': 'Server not ready - event loop closed'}), 500
                
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
        scheduled_time = data.get('scheduled_time')
        image_data = data.get('image')  # Base64 encoded image data
        
        logger.info(f"Received send_tweet request - Message: {message}, Scheduled: {scheduled_time}, Has Image: {bool(image_data)}")
        
        if not message and not image_data:
            logger.error("Missing message/image in request")
            return jsonify({'error': 'Message or image is required'}), 400
            
        # 生成消息唯一标识，用于防止重复发送
        message_hash = hashlib.md5(f"tweet_{message}_{scheduled_time}_{bool(image_data)}".encode()).hexdigest()
        
        # 检查是否是重复发送（5秒内）
        current_time = datetime.now().timestamp()
        if message_hash in recent_messages:
            last_time = recent_messages[message_hash]
            # 如果在5秒内重复发送，则拒绝
            if current_time - last_time < 5:
                logger.warning(f"Duplicate tweet detected within 5 seconds: {message_hash}")
                return jsonify({'error': 'Please wait a moment before sending the same tweet again'}), 429
        
        # 更新最近发送记录
        recent_messages[message_hash] = current_time
        
        # 清理旧记录（保留10分钟内的）
        expired_keys = [k for k, v in recent_messages.items() if current_time - v > 600]
        for key in expired_keys:
            del recent_messages[key]
            
        # 使用主事件循环
        if not main_loop:
            logger.error("Main event loop not initialized")
            return jsonify({'error': 'Server not ready'}), 500
            
        async def send_async():
            try:
                # 计算定时发送的延迟时间
                delay_info = None
                scheduled_datetime = None
                now = datetime.now()
                
                if scheduled_time:
                    try:
                        # 解析时间字符串，移除 'Z' 后缀
                        scheduled_time = scheduled_time.replace('Z', '')
                        scheduled_datetime = datetime.fromisoformat(scheduled_time)
                        
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
                        logger.error(f"Invalid scheduled time format: {scheduled_time}")
                        return jsonify({'error': f'Invalid scheduled time format: {str(e)}'}), 400
                
                # 发送推文
                result = await twitter_api.send_tweet(
                    message=message,
                    scheduled_time=scheduled_time if scheduled_time else None,
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