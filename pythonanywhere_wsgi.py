"""
PythonAnywhere WSGI配置文件
将此文件内容复制到 /var/www/jhfnetboy_pythonanywhere_com_wsgi.py
"""
import sys
import os
import logging
import traceback
import asyncio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wsgi")
logger.info("WSGI 初始化开始")

# 添加项目目录到sys.path
project_home = '/home/jhfnetboy/CBots'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path
logger.info(f"项目路径添加完成: {project_home}")

# 添加虚拟环境路径
virtualenv_path = '/home/jhfnetboy/.virtualenvs/cbots-env'
if os.path.exists(virtualenv_path + '/bin/activate_this.py'):
    with open(virtualenv_path + '/bin/activate_this.py') as file_:
        exec(file_.read(), dict(__file__=virtualenv_path + '/bin/activate_this.py'))
    logger.info(f"虚拟环境激活成功: {virtualenv_path}")
else:
    logger.warning(f"虚拟环境激活文件未找到: {virtualenv_path}/bin/activate_this.py")

# 创建并设置事件循环
try:
    logger.info("正在创建和设置事件循环...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.info("事件循环创建成功")
    
    # 导入并设置主事件循环
    try:
        from web_routes import set_main_loop
        set_main_loop(loop)
        logger.info("主事件循环设置成功")
    except Exception as e:
        logger.error(f"设置主事件循环失败: {e}")
        logger.error(traceback.format_exc())
except Exception as e:
    logger.error(f"创建事件循环失败: {e}")
    logger.error(traceback.format_exc())

# 导入Flask应用
try:
    logger.info("尝试导入pa_app...")
    from pa_app import app as application
    logger.info("成功导入pa_app!")
except Exception as e:
    logger.error(f"导入pa_app失败: {e}")
    logger.error(traceback.format_exc())
    
    # 创建备用Flask应用
    from flask import Flask, jsonify
    application = Flask(__name__)
    
    @application.route('/')
    def home():
        return "CBots服务遇到技术问题，请检查日志。"
    
    @application.route('/error')
    def error_details():
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})

logger.info("WSGI 初始化完成") 