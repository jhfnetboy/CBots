import os
import sys

def what(filename, h=None):
    """Determine the type of an image file."""
    if h is None:
        with open(filename, 'rb') as f:
            h = f.read(32)
    
    if not h:
        return None
    
    if h.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif h.startswith(b'\xff\xd8'):
        return 'jpeg'
    elif h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    elif h.startswith(b'BM'):
        return 'bmp'
    elif h.startswith(b'\x49\x49') or h.startswith(b'\x4D\x4D'):
        return 'tiff'
    elif h.startswith(b'II*\x00') or h.startswith(b'MM\x00*'):
        return 'tiff'
    elif h.startswith(b'\x00\x00\x01\x00'):
        return 'ico'
    elif h.startswith(b'\x00\x00\x02\x00'):
        return 'cur'
    elif h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return 'webp'
    
    return None

# 创建一个模拟的 imghdr 模块
class ImgHdr:
    def __init__(self):
        self.what = what

# 创建全局实例并注册到 sys.modules
imghdr = ImgHdr()
sys.modules['imghdr'] = imghdr 