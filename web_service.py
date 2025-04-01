from flask import Flask
import logging
from web_routes import web_bp, init_web_routes, set_main_loop
import asyncio
import os
from dotenv import load_dotenv
from telegram_api import TelegramAPI
from twitter_api import TwitterAPI

logger = logging.getLogger(__name__)

class WebService:
    def __init__(self, telegram_api: TelegramAPI, twitter_api: TwitterAPI):
        self.telegram_api = telegram_api
        self.twitter_api = twitter_api
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
        self.app.config['JSON_AS_ASCII'] = False
        # 根据环境变量MODE选择不同的端口
        mode = os.getenv('MODE', 'dev')
        if mode.lower() == 'dev':
            self.port = int(os.getenv('DEV_PORT', 8873))
            logger.info(f"Running in DEV mode on port {self.port}")
        else:
            self.port = int(os.getenv('PRD_PORT', 8872))
            logger.info(f"Running in PRODUCTION mode on port {self.port}")
        
        # 设置主事件循环
        self.loop = asyncio.get_event_loop()
        set_main_loop(self.loop)
        
        # 初始化路由
        self.init_routes()
        
    def init_routes(self):
        """初始化路由"""
        # 初始化路由
        init_web_routes(self.app, self.telegram_api.core.client)
        
    def run(self, startup_event=None):
        """运行 Web 服务"""
        try:
            # 确保 Telegram 服务正在运行
            if not self.telegram_api.is_running:
                logger.error("Telegram API service is not running")
                if startup_event:
                    startup_event.set()
                return
                
            # 设置启动事件
            if startup_event:
                startup_event.set()
                logger.info("Web service startup event set")
                
            # 启动服务
            logger.info(f"Starting web service on port {self.port}")
            self.app.run(host='0.0.0.0', port=self.port)
                
        except Exception as e:
            logger.error(f"Error running web service: {e}", exc_info=True)
            if startup_event:
                startup_event.set()  # 即使出错也设置事件，让主线程知道 