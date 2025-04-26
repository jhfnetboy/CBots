# PythonAnywhere兼容版web_service.py
from flask import Flask, render_template, jsonify, request
import logging
import os
import asyncio
import json
import traceback
from dotenv import load_dotenv
from web_routes import web_bp, set_main_loop

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建并配置事件循环
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
set_main_loop(loop)  # 设置web_routes模块中的主事件循环

# 创建Flask应用
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

# 版本信息
VERSION = "0.23.58"

# 配置应用
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
app.config['JSON_AS_ASCII'] = False

# 注册蓝图
try:
    app.register_blueprint(web_bp)
    logger.info("Successfully registered web_bp blueprint")
except Exception as e:
    logger.error(f"Error registering blueprint: {e}")

# 首页路由
@app.route('/')
def index():
    return render_template('telegram.html', version=VERSION)

# 状态路由
@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "version": VERSION,
        "environment": "PythonAnywhere",
        "event_loop": "initialized"
    })

# 发送消息API
@app.route('/api/send_message', methods=['POST'])
def send_message_api():
    """发送消息API - PythonAnywhere兼容版"""
    try:
        data = request.get_json()
        logger.info(f"收到发送消息请求: {data}")
        
        try:
            # 尝试导入并初始化Telegram API
            from telegram_api import TelegramAPI
            api = TelegramAPI()
            logger.info("Telegram API初始化成功")
            
            # 异步处理消息发送
            async def process_message():
                try:
                    # 尝试连接
                    await api.connect()
                    logger.info("Telegram API连接成功")
                    
                    # 发送消息
                    result = await api.send_message(
                        message=data.get('message'),
                        channel=data.get('channel'),
                        image_data=data.get('image'),
                        scheduled_time=data.get('scheduled_time')
                    )
                    
                    # 断开连接
                    await api.disconnect()
                    
                    return result
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    logger.error(traceback.format_exc())
                    return {"success": False, "error": str(e)}
            
            # 运行异步任务
            result = loop.run_until_complete(process_message())
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"处理消息请求失败: {e}")
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": str(e)})
            
    except Exception as e:
        logger.error(f"API请求处理失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

# 发送推文API
@app.route('/api/send_tweet', methods=['POST'])
def send_tweet_api():
    """发送推文API - PythonAnywhere兼容版"""
    try:
        data = request.get_json()
        logger.info(f"收到发送推文请求: {data}")
        
        try:
            # 尝试导入并初始化Twitter API
            from twitter_api import TwitterAPI
            api = TwitterAPI()
            logger.info("Twitter API初始化成功")
            
            # 异步处理推文发送
            async def process_tweet():
                try:
                    # 尝试连接
                    await api.connect()
                    logger.info("Twitter API连接成功")
                    
                    # 发送推文
                    result = await api.send_tweet(
                        message=data.get('message'),
                        scheduled_time=data.get('scheduled_time'),
                        image_data=data.get('image')
                    )
                    
                    # 断开连接
                    await api.disconnect()
                    
                    return result
                except Exception as e:
                    logger.error(f"发送推文失败: {e}")
                    logger.error(traceback.format_exc())
                    return {"success": False, "error": str(e)}
            
            # 运行异步任务
            result = loop.run_until_complete(process_tweet())
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"处理推文请求失败: {e}")
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": str(e)})
            
    except Exception as e:
        logger.error(f"API请求处理失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

# 错误处理
@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

# 应用初始化
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8872))
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port) 