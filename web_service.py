from flask import Flask
import logging
from web_routes import web_bp, init_web_routes, set_main_loop
import asyncio
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class WebService:
    def __init__(self, telegram_api, twitter_api):
        self.app = Flask(__name__)
        self.telegram_api = telegram_api
        self.twitter_api = twitter_api
        
        # 设置主事件循环
        loop = asyncio.get_event_loop()
        set_main_loop(loop)
        
        # 初始化路由
        init_web_routes(self.app, self.telegram_api.core.client)
        
        # 配置
        self.app.config['SECRET_KEY'] = 'your-secret-key-here'
        self.app.config['JSON_AS_ASCII'] = False
        
        # 从环境变量获取端口
        self.port = int(os.getenv('PORT', 5000))
        
    def run(self):
        """运行 Web 服务"""
        try:
            self.app.run(host='0.0.0.0', port=self.port)
        except Exception as e:
            logger.error(f"Error running web service: {e}", exc_info=True) 