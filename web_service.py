# PythonAnywhere兼容版web_service.py
from flask import Flask, render_template, jsonify, request, current_app
import logging
import os
import asyncio
import json
import traceback
import time
import threading
from dotenv import load_dotenv
from web_routes import web_bp, set_main_loop, get_or_create_loop

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 版本信息
VERSION = "0.24.61"

# 全局事件循环线程
event_loop_thread = None

# 创建Flask应用
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

# 配置应用
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
app.config['JSON_AS_ASCII'] = False

# 根据环境变量配置端口
MODE = os.getenv('MODE', 'prod').lower()
if MODE == 'dev':
    PORT = int(os.getenv('DEV_PORT', '8873'))
    logger.info(f"运行在开发模式，使用端口: {PORT}")
else:
    PORT = int(os.getenv('PRD_PORT', '8872'))
    logger.info(f"运行在生产模式，使用端口: {PORT}")

# 注册蓝图
try:
    app.register_blueprint(web_bp)
    logger.info("Successfully registered web_bp blueprint")
except Exception as e:
    logger.error(f"Error registering blueprint: {e}")

# 首页路由
@app.route('/')
def index():
    """主页路由"""
    return render_template('index.html')

# 状态路由
@app.route('/status')
def status():
    """服务状态检查"""
    global event_loop_thread
    
    # 获取事件循环状态
    loop = get_or_create_loop()
    
    return jsonify({
        "success": True,
        "version": VERSION,
        "time": time.time(),
        "event_loop": {
            "exists": loop is not None,
            "is_running": loop.is_running() if loop else False,
            "is_closed": loop.is_closed() if loop else True,
        },
        "thread": {
            "exists": event_loop_thread is not None,
            "is_alive": event_loop_thread.is_alive() if event_loop_thread else False,
        }
    })

# 发送消息API - 使用web_routes中新增的API端点
@app.route('/api/send_message', methods=['POST'])
def send_message():
    """发送消息API - 重定向到web_routes中的实现"""
    return web_bp.send_message()

# 发送推文API
@app.route('/api/send_tweet', methods=['POST'])
def send_tweet():
    """发送推文API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "未提供数据"}), 400
        
        # 提取消息内容
        message = data.get('message')
        media_urls = data.get('media_urls', [])
        
        # 验证必填字段
        if not message:
            return jsonify({"success": False, "error": "推文内容不能为空"}), 400
        
        logger.info(f"准备发送推文: {message[:100]}...")
        
        # 获取当前事件循环
        loop = get_or_create_loop()
        
        # 创建发送推文的异步函数
        async def send_tweet_task():
            try:
                # 这里应该调用Twitter API功能
                # 暂时模拟一个成功的结果
                await asyncio.sleep(1)  # 模拟API调用
                
                return {
                    "success": True, 
                    "message": "推文已成功发送",
                    "tweet_id": "simulated_id_" + str(int(time.time())),
                    "content": message,
                    "media_count": len(media_urls) if media_urls else 0
                }
            except Exception as e:
                logger.error(f"发送推文失败: {e}")
                logger.error(traceback.format_exc())
                return {"success": False, "error": str(e)}
        
        # 根据事件循环状态选择执行方式
        if loop.is_running():
            # 如果循环正在运行，使用run_coroutine_threadsafe
            logger.info("事件循环正在运行，使用run_coroutine_threadsafe发送推文")
            future = asyncio.run_coroutine_threadsafe(send_tweet_task(), loop)
            try:
                result = future.result(timeout=30)  # 30秒超时
                return jsonify(result)
            except Exception as e:
                logger.error(f"发送推文操作失败: {e}")
                return jsonify({"success": False, "error": str(e)})
        else:
            # 如果循环没有运行，使用run_until_complete
            logger.info("事件循环未运行，使用run_until_complete发送推文")
            try:
                result = loop.run_until_complete(
                    asyncio.wait_for(send_tweet_task(), timeout=30)
                )
                return jsonify(result)
            except Exception as e:
                logger.error(f"发送推文操作失败: {e}")
                logger.error(traceback.format_exc())
                return jsonify({"success": False, "error": str(e)})
    
    except Exception as e:
        logger.error(f"处理发送推文请求失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

# 错误处理
@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

def run_event_loop():
    """在独立线程中运行事件循环"""
    try:
        logger.info("开始初始化事件循环线程...")
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info(f"已创建新的事件循环: {loop}")
        
        # 设置为全局事件循环
        set_main_loop(loop)
        
        # 运行事件循环直到停止
        logger.info("启动事件循环...")
        loop.run_forever()
        
        # 清理工作
        logger.info("事件循环已停止，进行清理...")
        pending = asyncio.all_tasks(loop)
        if pending:
            logger.info(f"取消 {len(pending)} 个待处理任务")
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        
        loop.close()
        logger.info("事件循环已关闭")
    
    except Exception as e:
        logger.error(f"事件循环线程出错: {e}")
        logger.error(traceback.format_exc())

# 应用初始化
if __name__ == '__main__':
    try:
        logger.info(f"启动服务，版本: {VERSION}")
        
        # 创建并启动事件循环线程
        event_loop_thread = threading.Thread(target=run_event_loop, daemon=True, name="EventLoopThread")
        event_loop_thread.start()
        logger.info(f"事件循环线程已启动: {event_loop_thread.name}")
        
        # 等待事件循环初始化
        time.sleep(1)
        
        # 启动Flask应用
        logger.info(f"启动Web服务在端口: {PORT}...")
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭...")
    
    except Exception as e:
        logger.error(f"启动服务时发生错误: {e}")
        logger.error(traceback.format_exc()) 