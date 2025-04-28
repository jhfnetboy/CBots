# CBots 变更日志

## v0.8.7 (2024-07-25)
- 迁移到 Telegram Bot API 以兼容 PythonAnywhere
  - 创建了 `bot_api_core.py` 使用 `python-telegram-bot` 库。
  - 修改了 `web_service.py` 以集成 `BotAPICore` 并添加 webhook 路由。
  - 调整了 `bot_api_core.py`，移除 `start()` 方法，启动由入口控制。
  - 修改了 `main.py`，使其仅在本地运行时启动 polling 模式用于测试。
  - 更新了 `requirements.txt`，添加 `python-telegram-bot`，移除 `telethon` 和 `aiohttp`。
  - 更新了 `pythonanywhere_deployment.md`，适配 webhook 部署流程。

## v0.8.6 (2024-07-24)
- 修复了@消息处理功能
  - 添加了缺失的`is_message_to_me`函数用于检测@消息
  - 添加了`handle_mentioned_message`函数处理@消息的响应
  - 完善了消息处理流程，确保所有类型的消息都能正确响应
  - 确认mute和unmute功能可正常工作

## v0.8.5 (2024-07-23)
- 解决了Web服务启动和命令处理问题
  - 修改了`main.py`中的`start_web_service`函数，确保正确启动Web服务
  - 添加了端口测试机制，验证服务是否成功启动
  - 增强了`/pass`命令处理，确保能正确响应密码请求
  - 添加了`/version`命令显示当前版本号
  - 优化了日志输出，提供更详细的状态信息

## v0.8.4 (2024-07-22)
- 解决了SQLite数据库锁定问题
  - 修改了`main.py`中的服务启动逻辑，使用全局`TelegramCore`实例
  - 优化了`telegram_api.py`中的`start`方法，增强了对已启动核心服务的检测
  - 增加了更详细的日志输出，便于故障排查
  - 延长了服务启动之间的等待时间，确保服务正常初始化

## v0.8.3 (2024-07-21)
- 修复了telegram_api_service启动问题
  - 将错误的`start_api_server()`调用替换为正确的`start()`异步方法
  - 添加了更完善的异步事件循环处理
  - 改进了错误记录，添加了traceback输出以便更好地诊断问题

## v0.8.2 (2024-07-20)
- 删除了不必要的文件以简化项目结构
  - 移除了`twitter_auth.py`, `twitter_api.py`和`twitter_core.py`
  - 删除了`webhooks.py`和`handler.py`
- 简化了导入和依赖关系
- 仅保留了telegram核心功能

## v0.8.1 (2024-07-19)
- 添加了`tweepy_patch.py`解决imghdr模块在Python 3.13中的兼容性问题
- 更新了环境变量加载机制
- 优化了日志记录格式

## v0.8.0 (2024-07-18)
- 初始化精简版MuteBot
- 仅保留禁言和验证功能
- 移除了Twitter相关功能
- 实现了基本的Telegram核心和API服务

## 0.25.01 (2024-06-01)
- 修复main.py中无法导入WebService类的问题
- 更改导入方式，使用import web_service替代from web_service import WebService
- 修改telegram_api_service函数中实例化TelegramAPI的方式

## 0.25.00 (2024-06-01)
尝试一个简单的mutebot版本，在当下功能进行裁剪：
1. 去掉twitter所有功能
   - 移除了TwitterCore和TwitterAPI相关代码
   - 从main.py中移除Twitter服务启动
2. 去掉telegram bot复杂功能，只保留核心功能
   - 仅保留/pass命令来获得当日密码
   - 保留新用户进入自动mute功能
   - 保留私聊bot发送密码后解除mute功能
3. 简化web页面
   - 创建简单的状态显示页面status.html
   - 页面只显示服务状态和版本
4. 添加tweepy补丁解决Python 3.13兼容性问题
   - 创建tweepy_patch.py模块使用mimetypes替代imghdr
5. 提供PythonAnywhere部署指南
   - 创建pythonanywhere_deployment.md详细说明部署步骤

修改的文件：
- web_service.py：更新版本号至0.25.00，移除Twitter相关功能
- message_handlers.py：精简为只保留核心功能
- main.py：移除Twitter相关功能
- tweepy_patch.py：新增模块解决兼容性问题
- templates/status.html：新增简化的状态页面
- pythonanywhere_deployment.md：新增部署指南

## 版本 0.24.62 (2024-06-01)
- 添加tweepy_patch.py模块，修复Python 3.13环境下imghdr模块缺失的问题
- 使用mimetypes模块替代imghdr模块，确保tweepy库正常运行
- 更新web_service.py版本号
- 修改main.py，在启动时优先导入tweepy_patch模块

## 版本 0.24.61 (2024-06-01)
- 优化web_service.py中的端口配置，根据环境变量MODE动态选择不同端口
- 开发环境(MODE=dev)使用DEV_PORT环境变量(默认8873)
- 生产环境使用PRD_PORT环境变量(默认8872)
- 提高了配置灵活性，便于在不同环境中部署和测试

## 版本 0.23.53 (2024-04-01)
- 优化图片发送功能，强制使用文档模式发送图片，绕过Telegram的扩展名验证
- 移除Base64数据的详细日志记录，提高安全性和日志可读性
- 简化图片发送流程，统一使用document方式发送

## 版本 0.23.52 (2024-04-01)
- 完全重写图片发送逻辑，确保图片以照片格式而非文档格式发送
- 添加图片格式自动转换功能，将所有图片格式转换为 JPEG 格式
- 使用 PIL 库处理透明图片，在白色背景上合成图片，保持视觉效果
- 强制使用 .jpeg 扩展名，确保与 Telegram API 的最佳兼容性
- 改进图片显示效果，文字在上方，图片在下方，无文件名和"Open with"按钮

## 版本 0.23.51 (2024-04-01)
- 修复循环导入（circular import）问题，恢复 message_handlers.py 中独立的版本号定义
- 优化模块依赖结构，确保系统稳定启动

## 版本 0.23.50 (2024-04-01)
- 优化图片发送功能，增加自动故障恢复机制
- 当作为照片发送失败时，自动尝试作为文档发送
- 强制将非 jpg/jpeg 格式图片的扩展名转换为 jpeg，提高兼容性
- 统一版本管理，message_handlers.py 从 web_routes.py 导入版本号

## 版本 0.23.49 (2024-04-01)
- 优化图片发送格式，改为正常图文样式显示
- 移除 force_document 参数，使图片显示为照片而非文档
- 修复图片在消息中显示为小图标和"Open with"选项的问题
- 改进图片发送逻辑，确保图片正确显示

## 版本 0.23.48 (2024-04-01)
- 修复图片发送时的 "The extension of the photo is invalid" 错误
- 强制使用 force_document=True 参数发送图片，绕过 Telethon 对照片格式的验证
- 添加对图片文件扩展名的自动检查和修正，确保扩展名有效
- 改进错误处理和日志记录

## 版本 0.23.47 (2024-04-01)
- 优化防重复发送机制，将时间窗口从30秒减少到5秒
- 简化消息哈希生成逻辑，移除日期字符串，避免错误判定为重复消息
- 提高用户体验，减少重复点击的等待时间

## 版本 0.23.46 (2024-04-01)
- 修复私聊 /PNTs 命令未能正确处理的问题，优化私聊消息处理逻辑
- 修改 /pass 命令，允许在公开群组直接回复当日密码
- 优化图片发送格式，改为正常图文消息格式，不再以文档形式发送
- 为消息发送和推文发送接口添加防重复点击机制，30秒内相同内容不允许重复发送

## 版本 0.23.45 (2024-04-01)
- 取消对 Twitter 服务启动的注释，恢复 Twitter 功能
- 重构命令处理逻辑，为每个命令创建独立的处理函数
- 更新命令帮助信息，明确指出哪些命令可在公共群组使用，哪些需要私聊
- 添加 /price、/event、/task 命令在公共群组显示相关信息
- 改进 /pnts 和 /account 命令，在私聊中显示详细信息，在公共群组提示私聊
- 保持现有的每日密码、自动禁言新用户和私聊解禁用户的功能不变

## 版本 0.23.44 (2024-04-01)
- 修复图片发送扩展名问题，使用 force_document=True 参数强制作为文档发送图片
- 更新 web_service.py 中的端口配置，根据 MODE 环境变量选择不同的端口
- 开发环境 (MODE=dev) 使用 DEV_PORT (默认 8873)
- 生产环境使用 PRD_PORT (默认 8872)

## 版本 0.23.43 (2024-04-01)
- 修改 web_service.py 中的端口配置，从环境变量加载 PORT，默认为 8873
- 优化项目结构，明确 image_sender.py 的职责和接口

## 版本 0.23.42 (2024-04-01)
- 修复 Telegram 发送图片时的扩展名问题
- 创建独立的图片发送功能模块 (image_sender.py)
- 确保图片 BytesIO 对象带有正确的文件名和扩展名属性
- 优化图片处理逻辑，支持从 Base64 和 URL 正确提取扩展名
- 统一图片处理方式，使用固定的扩展名格式 (jpeg) 确保兼容性
- 改进错误处理和日志记录

## v0.8.3 (2024-07-21)
- 修复了telegram_api_service启动问题
  - 将错误的`start_api_server()`调用替换为正确的`start()`异步方法
  - 添加了更完善的异步事件循环处理
  - 改进了错误记录，添加了traceback输出以便更好地诊断问题

## v0.8.2 (2024-07-20)
- 删除了不必要的文件以简化项目结构
  - 移除了`twitter_auth.py`, `twitter_api.py`和`twitter_core.py`
  - 删除了`webhooks.py`和`handler.py`
- 简化了导入和依赖关系
- 仅保留了telegram核心功能

## v0.8.1 (2024-07-19)
- 添加了`tweepy_patch.py`解决imghdr模块在Python 3.13中的兼容性问题
- 更新了环境变量加载机制
- 优化了日志记录格式

## v0.8.0 (2024-07-18)
- 初始化精简版MuteBot
- 仅保留禁言和验证功能
- 移除了Twitter相关功能
- 实现了基本的Telegram核心和API服务 