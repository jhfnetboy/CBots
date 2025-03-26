from http.server import BaseHTTPRequestHandler
import sys
import os

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import app
import json

def handler(event, context):
    """Handle incoming Netlify Function requests"""
    try:
        # 获取请求信息
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        body = event.get('body', '')
        headers = event.get('headers', {})
        
        # 创建 WSGI 环境
        environ = {
            'REQUEST_METHOD': http_method,
            'PATH_INFO': path,
            'QUERY_STRING': event.get('queryStringParameters', {}),
            'wsgi.input': body,
            'wsgi.errors': '',
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        
        # 添加请求头
        for key, value in headers.items():
            environ[f'HTTP_{key.upper().replace("-", "_")}'] = value
            
        # 处理请求
        with app.request_context(environ):
            try:
                # 设置正确的路径
                app.request.path = path
                app.request.url = f"https://{headers.get('host', '')}{path}"
                response = app.full_dispatch_request()
            except Exception as e:
                app.logger.error(f"Error handling request: {str(e)}")
                response = app.handle_exception(e)
            
            # 构建响应
            return {
                'statusCode': response.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    **dict(response.headers)
                },
                'body': response.get_data(as_text=True)
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        } 