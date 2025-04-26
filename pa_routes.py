"""
PythonAnywhere兼容的API路由
处理Telegram消息发送请求
"""
import os
import json
import time
import logging
import traceback
import asyncio
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

# 导入PythonAnywhere兼容的Telegram API
from pa_telegram import TelegramAPI

# 创建蓝图
pa_api = Blueprint('pa_api', __name__)

# 配置日志
logger = logging.getLogger(__name__)

# 全局API实例
telegram_api = None

@pa_api.before_app_first_request
def initialize_apis():
    """初始化API服务"""
    global telegram_api
    
    try:
        logger.info("初始化Telegram API...")
        telegram_api = TelegramAPI()
        logger.info("API初始化完成")
    except Exception as e:
        logger.error(f"初始化API服务失败: {e}")
        logger.error(traceback.format_exc())

@pa_api.route('/api/status', methods=['GET'])
async def get_status():
    """获取服务状态"""
    global telegram_api
    
    # 重置状态
    status = {
        "version": current_app.config.get('VERSION', 'unknown'),
        "server": "running",
        "telegram": "not_ready",
        "timestamp": datetime.now().isoformat()
    }
    
    # 检查Telegram服务
    try:
        if telegram_api:
            # 尝试连接
            connected = await telegram_api.connect()
            status["telegram"] = "ready" if connected else "not_connected"
            
            # 连接后立即断开，避免长时间连接
            await telegram_api.disconnect()
        else:
            status["telegram"] = "not_initialized"
    except Exception as e:
        logger.error(f"获取Telegram状态失败: {e}")
        status["telegram"] = f"error: {str(e)}"
    
    logger.info(f"服务状态: {status}")
    return jsonify(status)

@pa_api.route('/api/send', methods=['POST'])
async def send_message():
    """发送消息API"""
    global telegram_api
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效请求: 缺少JSON数据"}), 400
        
        # 记录请求数据
        logger.info(f"收到发送请求: {json.dumps(data, ensure_ascii=False)[:200]}...")
        
        # 提取参数
        group = data.get('channel') or data.get('group')
        message = data.get('message', '')
        image = data.get('image')
        scheduled_time = data.get('scheduled_time') or data.get('schedule_time')
        
        # 参数验证
        if not group:
            return jsonify({"success": False, "error": "缺少必要参数: channel/group"}), 400
        
        if not message and not image:
            return jsonify({"success": False, "error": "消息和图片不能同时为空"}), 400
        
        # 确保API已初始化
        if not telegram_api:
            logger.warning("API尚未初始化，尝试重新初始化")
            telegram_api = TelegramAPI()
        
        # 发送消息
        result = await telegram_api.send_message(
            message=message,
            channel=group,
            image_data=image,
            scheduled_time=scheduled_time
        )
        
        # 发送完成后断开连接
        await telegram_api.disconnect()
        
        # 处理结果
        if result.get('success'):
            logger.info(f"消息发送成功: {result}")
            return jsonify(result)
        else:
            logger.error(f"消息发送失败: {result}")
            return jsonify(result), 500
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"处理发送请求时出错: {error_msg}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500

@pa_api.route('/api/logs', methods=['GET'])
def get_logs():
    """获取最近的日志"""
    try:
        # 最大返回行数
        max_lines = int(request.args.get('lines', 100))
        max_lines = min(max_lines, 1000)  # 限制最大行数
        
        # 读取应用日志（这里假设日志文件位置）
        log_path = os.path.join(os.environ.get('LOG_DIR', '/tmp'), 'pa_app.log')
        
        # 如果日志文件不存在，返回空数组
        if not os.path.exists(log_path):
            logger.warning(f"日志文件不存在: {log_path}")
            return jsonify({"logs": [], "error": "日志文件不存在"})
        
        # 读取最后N行
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                logs = lines[-max_lines:] if len(lines) > max_lines else lines
                return jsonify({"logs": logs})
        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")
            return jsonify({"logs": [], "error": f"读取日志失败: {str(e)}"})
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"获取日志时出错: {error_msg}")
        return jsonify({"logs": [], "error": error_msg}), 500 