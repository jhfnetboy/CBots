# PythonAnywhere 部署指南 - MuteBot (Bot API Webhook 模式)

本指南将帮助您在 PythonAnywhere 上部署 MuteBot 服务，使用 Telegram Bot API 的 Webhook 模式。
此模式兼容 PythonAnywhere 的免费账户网络限制。
如果你想在本地测试，只需运行 source venv/bin/activate && python main.py，它会自动进入 polling 模式。

## 前提条件

1.  拥有 PythonAnywhere 账号（免费账号即可）
2.  拥有 Telegram Bot Token (从 BotFather 获取)
3.  准备好您的 PythonAnywhere Web App 域名 (e.g., `yourusername.pythonanywhere.com`)

## 步骤 1: 获取代码并设置环境

1.  登录 PythonAnywhere Dashboard。
2.  打开一个 **Bash Console**。
3.  克隆代码仓库 (如果尚未克隆):
    ```bash
    cd ~
    # git clone https://github.com/your-repo/mutebot.git # Replace with your repo URL
    cd mutebot # 进入项目目录
    ```
4.  创建并激活虚拟环境 (使用您希望的 Python 版本, 推荐 3.8+):
    ```bash
    python3.11 -m venv venv # Or python3.9, python3.10 etc.
    source venv/bin/activate
    ```
5.  安装依赖:
    ```bash
    pip install -r requirements.txt
    ```

## 步骤 2: 配置环境变量

1.  在 PythonAnywhere **Files** 选项卡中，导航到您的项目目录 (`/home/yourusername/mutebot`)。
2.  创建或编辑 `.env` 文件，确保包含以下内容:
    ```dotenv
    TELEGRAM_BOT_TOKEN=你的Bot_Token
    TELEGRAM_GROUP=@你的目标群组用户名或ID # 用于解禁用户
    WEBHOOK_URL=https://yourusername.pythonanywhere.com # 替换为你的 PythonAnywhere 域名
    # FLASK_SECRET_KEY=your-secret-key # 可选，如果需要 Flask session
    # MODE=prod # 可选, web_service.py 已默认为生产
    ```
    **重要:** `WEBHOOK_URL` 必须是你的 PythonAnywhere Web App 的 HTTPS 地址。

## 步骤 3: 配置 Web App 和 WSGI 文件

1.  在 Dashboard 中点击 **Web** 选项卡。
2.  如果还没有 Web App，点击 **Add a new web app**:
    *   确认域名。
    *   选择 **Manual configuration**。
    *   选择与您创建 venv 时相同的 Python 版本 (e.g., Python 3.11)。
3.  **配置 Virtualenv**:
    *   在 "Virtualenv" 部分，输入虚拟环境的路径: `/home/yourusername/mutebot/venv`。
4.  **配置 WSGI 文件**:
    *   点击 "WSGI configuration file" 链接 (通常是 `/var/www/yourusername_pythonanywhere_com_wsgi.py`)。
    *   将其内容替换为:
        ```python
        import sys
        import os

        # 添加项目路径到 sys.path
        project_home = '/home/yourusername/mutebot' # *** 修改为你的项目路径 ***
        if project_home not in sys.path:
            sys.path.insert(0, project_home)

        # 加载项目目录下的 .env 文件
        from dotenv import load_dotenv
        dotenv_path = os.path.join(project_home, '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
            print(f"Loaded environment variables from {dotenv_path}") # Optional: for debugging
        else:
            print(f"Warning: .env file not found at {dotenv_path}") # Optional: for debugging

        # 设置 PYTHONPATH 环境变量 (可选, 但有时有帮助)
        # os.environ['PYTHONPATH'] = project_home

        # 导入 Flask 应用
        try:
            from web_service import app as application
            print("Successfully imported Flask application from web_service") # Optional: for debugging
        except Exception as e:
            # Log the error for debugging in the WSGI error log
            print(f"Error importing Flask application: {e}")
            import traceback
            traceback.print_exc()
            raise # Re-raise the exception so PythonAnywhere logs it
        ```
    *   **务必** 将 `yourusername` 替换为你的 PythonAnywhere 用户名。
    *   保存文件。

## 步骤 4: 设置 Telegram Webhook

1.  回到 PythonAnywhere 的 **Web** 选项卡。
2.  点击 **Reload yourusername.pythonanywhere.com** 按钮应用 WSGI 配置并启动 Web App。
3.  在 **Bash Console** 中 (确保 venv 已激活)，运行一次性脚本来设置 webhook (或者你可以本地运行这个 Python 片段):
    ```python
    import os
    from telegram import Bot
    from dotenv import load_dotenv

    load_dotenv() # Load .env

    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')

    if not TOKEN or not WEBHOOK_URL:
        print("Error: TELEGRAM_BOT_TOKEN or WEBHOOK_URL not found in .env")
    else:
        hook_url = f"{WEBHOOK_URL}/{TOKEN}" # The webhook URL must match the route in web_service.py
        bot = Bot(token=TOKEN)
        try:
            bot.set_webhook(url=hook_url)
            print(f"Webhook set successfully to: {hook_url}")
        except Exception as e:
            print(f"Error setting webhook: {e}")
    ```
4.  **重要:** 确保 `hook_url` (即 `https://yourusername.pythonanywhere.com/YOUR_BOT_TOKEN`) 与 `web_service.py` 中定义的路由完全匹配。

## 步骤 5: 检查日志

*   **Web Server Log:** 在 PythonAnywhere Web 选项卡下，查看 "Log files" -> "Server log"。这里会显示 WSGI 服务器的启动信息和 HTTP 请求日志。
*   **Error Log:** 查看 "Log files" -> "Error log"。这里会显示 WSGI 文件加载错误或 Flask 应用运行时错误。
*   **Bot Log:** 查看 `/home/yourusername/mutebot/bot.log` (在 Files 选项卡或 Console 中 `cat bot.log`)。这是我们代码中配置的日志文件，记录 Bot 的运行信息。

## 完成!

现在，你的 MuteBot 应该通过 Webhook 在 PythonAnywhere 上运行了。新消息会触发 Telegram 调用你的 Webhook URL，然后由你的 Flask 应用处理。
你不再需要手动在 Console 中运行 `python main.py`，也不需要在 Tasks 中设置定时任务来启动它。

## 保持服务运行

由于 PythonAnywhere 免费账户有使用限制，建议：

1. 每3个月登录一次您的账户以保持活跃
2. 设置额外的定时任务，每天ping一次您的Web服务以保持它的运行状态

---

祝您使用愉快！如有任何问题，请参考 [PythonAnywhere 帮助文档](https://help.pythonanywhere.com/) 或联系本项目维护者。 