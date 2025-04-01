"""
独立的图片发送功能模块
不影响核心功能，用于处理图片发送逻辑
"""

import logging
import os
import time
import base64
from io import BytesIO
import aiohttp
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageSender:
    """独立的图片发送处理类"""
    
    @staticmethod
    async def prepare_image_from_base64(image_data):
        """从 Base64 数据准备图片"""
        try:
            # 提取 Base64 图片的内容类型
            content_type = image_data.split(';')[0].split(':')[1]
            logger.info(f"Image content type: {content_type}")
            
            # 提取扩展名
            ext = content_type.split('/')[1]
            logger.info(f"Extracted extension from content type: {ext}")
            # 强制使用 jpeg 扩展名，确保最佳兼容性
            ext = 'jpeg'
            
            # 创建文件名
            file_name = f"image_{int(time.time())}.{ext}"
            logger.info(f"Generated filename: {file_name}")
            
            # 从Base64数据中提取图片数据 - 不记录具体base64内容
            logger.info("Decoding base64 image data...")
            image_bytes = base64.b64decode(image_data.split(',')[1])
            logger.info(f"Decoded base64 image data, size: {len(image_bytes)}")
            
            # 尝试转换为JPEG格式（如果需要的话）
            try:
                from PIL import Image
                from io import BytesIO
                # 尝试打开图片
                image = Image.open(BytesIO(image_bytes))
                # 如果不是JPEG，转换为JPEG
                if image.format != 'JPEG':
                    logger.info(f"Converting image from {image.format} to JPEG")
                    # 创建一个新的BytesIO对象
                    jpeg_buffer = BytesIO()
                    # 如果图片有透明通道，需要处理
                    if image.mode == 'RGBA':
                        # 创建白色背景
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        # 将原图合成到背景上
                        background.paste(image, mask=image.split()[3])
                        # 保存为JPEG
                        background.save(jpeg_buffer, 'JPEG')
                    else:
                        # 直接保存为JPEG
                        image.convert('RGB').save(jpeg_buffer, 'JPEG')
                    # 获取转换后的字节
                    image_bytes = jpeg_buffer.getvalue()
                    logger.info(f"Converted image size: {len(image_bytes)} bytes")
            except ImportError:
                logger.warning("PIL not installed, skipping image conversion")
            except Exception as e:
                logger.warning(f"Failed to convert image: {e}, using original bytes")
            
            # 创建 BytesIO 对象并设置文件名
            image_file = BytesIO(image_bytes)
            image_file.name = file_name
            logger.info(f"Created BytesIO object with name: {file_name}")
            
            return image_file
        except Exception as e:
            logger.error(f"Error processing base64 image data: {e}")
            raise

    @staticmethod
    async def prepare_image_from_url(image_url):
        """从 URL 准备图片"""
        try:
            # 下载图片URL
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to download image from URL: {resp.status}")
                        raise Exception(f"Failed to download image from URL: {resp.status}")
                    
                    # 获取图片字节数据
                    image_bytes = await resp.read()
                    logger.info(f"Downloaded image size: {len(image_bytes)} bytes")
                    
                    # 强制使用 jpeg 扩展名，确保最佳兼容性
                    ext = 'jpeg'
                    logger.info(f"Using extension: {ext}")
                    
                    # 创建文件名
                    file_name = f"image_{int(time.time())}.{ext}"
                    logger.info(f"Generated filename for URL image: {file_name}")
                    
                    # 尝试转换为JPEG格式
                    try:
                        from PIL import Image
                        from io import BytesIO
                        # 尝试打开图片
                        image = Image.open(BytesIO(image_bytes))
                        # 如果不是JPEG，转换为JPEG
                        if image.format != 'JPEG':
                            logger.info(f"Converting image from {image.format} to JPEG")
                            # 创建一个新的BytesIO对象
                            jpeg_buffer = BytesIO()
                            # 如果图片有透明通道，需要处理
                            if image.mode == 'RGBA':
                                # 创建白色背景
                                background = Image.new('RGB', image.size, (255, 255, 255))
                                # 将原图合成到背景上
                                background.paste(image, mask=image.split()[3])
                                # 保存为JPEG
                                background.save(jpeg_buffer, 'JPEG')
                            else:
                                # 直接保存为JPEG
                                image.convert('RGB').save(jpeg_buffer, 'JPEG')
                            # 获取转换后的字节
                            image_bytes = jpeg_buffer.getvalue()
                            logger.info(f"Converted image size: {len(image_bytes)} bytes")
                    except ImportError:
                        logger.warning("PIL not installed, skipping image conversion")
                    except Exception as e:
                        logger.warning(f"Failed to convert image: {e}, using original bytes")
                    
                    # 创建 BytesIO 对象并设置文件名
                    image_file = BytesIO(image_bytes)
                    image_file.name = file_name
                    logger.info(f"Created BytesIO object from URL with name: {file_name}")
                    
                    return image_file
        except Exception as e:
            logger.error(f"Error downloading image from URL: {e}")
            raise

    @staticmethod
    async def send_image_message(client, entity, message, image_file, reply_to=None):
        """发送带图片的消息"""
        try:
            if not image_file:
                raise ValueError("Image file is required")
                
            logger.info(f"Sending message with image: {image_file.name}")
            
            # 确保图片文件有名称属性，这对 Telethon 很重要
            if not hasattr(image_file, 'name'):
                file_name = f"image_{int(time.time())}.jpeg"
                image_file.name = file_name
                logger.info(f"Image file had no name, set to: {file_name}")
            
            # 检查文件扩展名，确保是 .jpg 或 .jpeg (Telethon 对这些格式支持最好)
            original_name = image_file.name
            file_base, file_ext = os.path.splitext(image_file.name)
            file_ext = file_ext.lower().lstrip('.')
            
            # 如果不是 jpeg/jpg 格式，强制转换为 jpeg
            if file_ext not in ['jpg', 'jpeg']:
                image_file.name = f"{file_base}.jpeg"
                logger.info(f"Changed image file extension from {original_name} to {image_file.name}")
            
            # 记录图片详情
            logger.info(f"Image details - Name: {image_file.name}, Size: {len(image_file.getvalue())} bytes")
            
            # 从 BytesIO 对象提取原始字节，确保数据完整
            image_bytes = image_file.getvalue()
            
            # 创建新的 BytesIO 对象，避免之前对象可能的读取位置问题
            fresh_image = BytesIO(image_bytes)
            fresh_image.name = image_file.name
            
            # 尝试两种发送方式，先尝试作为照片发送，失败则作为文档发送
            try:
                # 更简单的方法：始终作为文档发送，绕过扩展名验证
                if reply_to:
                    logger.info(f"Sending image as document to topic {reply_to}")
                    result = await client.send_file(
                        entity=entity,
                        file=fresh_image,
                        caption=message,
                        reply_to=reply_to,
                        force_document=True  # 强制作为文档发送
                    )
                else:
                    logger.info("Sending image as document")
                    result = await client.send_file(
                        entity=entity,
                        file=fresh_image,
                        caption=message,
                        force_document=True  # 强制作为文档发送
                    )
                logger.info(f"Image message sent successfully as document! ID: {result.id}")
                return result.id
            except Exception as e:
                logger.error(f"Failed to send image: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error sending image message: {e}")
            raise 