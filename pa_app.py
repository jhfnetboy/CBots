"""
专用于PythonAnywhere部署的Flask应用
此文件优化了初始化流程，避免阻塞WSGI服务器
"""
import os
import time
import json
import logging
import traceback
from flask import Flask, jsonify, request, render_template, redirect, url_for
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("pa_app模块加载中...")

# 加载环境变量
try:
    load_dotenv()
    logger.info("环境变量加载成功")
except Exception as e:
    logger.error(f"环境变量加载失败: {e}")

# 创建Flask应用
app = Flask(__name__, 
          static_folder='static',
          template_folder='templates')

# 版本信息
VERSION = "0.23.58"
app.config['VERSION'] = VERSION

# 应用状态
app_status = {
    "app_version": VERSION,
    "telegram_api": "not_initialized",
    "twitter_api": "not_initialized",
    "start_time": time.time(),
    "environment": "PythonAnywhere",
    "last_error": None
}

# 路由注册
try:
    # 尝试注册现有的蓝图
    from web_routes import web_bp
    app.register_blueprint(web_bp)
    logger.info("成功注册web_bp蓝图")
except Exception as e:
    logger.error(f"注册蓝图失败: {e}")
    logger.error(traceback.format_exc())

# 首页路由
@app.route('/')
def index():
    try:
        return render_template('telegram.html', version=VERSION)
    except Exception as e:
        logger.error(f"渲染首页模板失败: {e}")
        return f"CBots服务 - 版本 {VERSION}"

# API路由
@app.route('/api/status')
def api_status():
    """服务状态API"""
    status = {
        "version": VERSION,
        "uptime": int(time.time() - app_status["start_time"]),
        "environment": "PythonAnywhere",
        "timestamp": int(time.time()),
        "services": {
            "web": "running",
            "telegram_api": app_status["telegram_api"],
            "twitter_api": app_status["twitter_api"]
        }
    }
    return jsonify(status)

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
            import asyncio
            
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
                    
                    # 更新状态
                    app_status["telegram_api"] = "connected"
                    
                    return result
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    logger.error(traceback.format_exc())
                    app_status["last_error"] = str(e)
                    return {"success": False, "error": str(e)}
            
            # 在PythonAnywhere环境中，必须手动创建事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            result = loop.run_until_complete(process_message())
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"处理消息请求失败: {e}")
            logger.error(traceback.format_exc())
            app_status["last_error"] = str(e)
            return jsonify({"success": False, "error": str(e)})
            
    except Exception as e:
        logger.error(f"API请求处理失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/logs')
def view_logs():
    """查看最近日志"""
    log_entries = []
    
    # 创建一个简单的内存日志查看器
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'stream'):
            try:
                log_entries.append("=== 日志内容 ===")
                log_entries.append(str(handler.stream.getvalue() if hasattr(handler.stream, 'getvalue') else "无法获取日志内容"))
            except:
                log_entries.append("无法读取日志流")
    
    return jsonify({
        "logs": log_entries,
        "status": app_status
    })

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "页面未找到", "status": 404}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"服务器错误: {e}")
    app_status["last_error"] = str(e)
    return jsonify({"error": "服务器内部错误", "details": str(e)}), 500

# 模块初始化完成
logger.info("pa_app模块加载完成")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8872))
    app.run(host='0.0.0.0', port=port) 