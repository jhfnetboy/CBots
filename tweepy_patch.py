"""
这个模块用于修补tweepy包中的api.py模块，解决Python 3.13中imghdr模块缺失的问题。
它通过替换imghdr.what函数为mimetypes模块的实现来实现兼容性。
"""

import sys
import logging
import mimetypes
import contextlib
import os

logger = logging.getLogger(__name__)

def apply_patch():
    """应用tweepy补丁，替换imghdr.what函数"""
    try:
        # 检查是否是Python 3.13
        if sys.version_info.major == 3 and sys.version_info.minor >= 13:
            logger.info("检测到Python 3.13或更高版本，应用tweepy补丁...")
            
            # 创建imghdr模块的模拟实现
            class ImghdrModule:
                @staticmethod
                def what(file, h=None):
                    """模拟imghdr.what函数，使用mimetypes代替"""
                    if h is not None:
                        # 无法处理字节头，返回None
                        return None
                    
                    if isinstance(file, str):
                        # 文件路径
                        mime_type, _ = mimetypes.guess_type(file)
                    else:
                        # 文件对象，尝试获取名称
                        try:
                            name = getattr(file, 'name', None)
                            if name:
                                mime_type, _ = mimetypes.guess_type(name)
                            else:
                                # 无法判断，返回None
                                return None
                        except Exception:
                            return None
                    
                    # 将MIME类型转换为imghdr格式的图像类型
                    if mime_type:
                        if mime_type == 'image/jpeg':
                            return 'jpeg'
                        elif mime_type == 'image/png':
                            return 'png'
                        elif mime_type == 'image/gif':
                            return 'gif'
                        elif mime_type == 'image/webp':
                            return 'webp'
                        elif mime_type == 'image/tiff':
                            return 'tiff'
                    
                    return None
            
            # 添加模拟模块到sys.modules
            sys.modules['imghdr'] = ImghdrModule()
            logger.info("成功应用tweepy补丁，替换imghdr模块")
            
            # 确保mimetypes数据库已初始化
            mimetypes.init()
            
            return True
    except Exception as e:
        logger.error(f"应用tweepy补丁失败: {e}")
    
    return False

# 在导入时自动应用补丁
patched = apply_patch() 