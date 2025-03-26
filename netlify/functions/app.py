from http.server import BaseHTTPRequestHandler
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
            
        # 处理根路径重定向
        if path == '/':
            return {
                'statusCode': 302,
                'headers': {'Location': '/telegram'},
                'body': ''
            }
        
        # 处理请求
        with app.request_context(environ):
            response = app.full_dispatch_request()
            
            # 构建响应
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True)
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        } 